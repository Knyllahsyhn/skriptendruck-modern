/**
 * Skriptendruck Dashboard – JavaScript
 */

/**
 * Zeigt eine Toast-Benachrichtigung an.
 * @param {string} message - Nachricht
 * @param {string} type - 'success', 'danger', 'warning', 'info'
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const iconMap = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-circle-fill',
        info: 'bi-info-circle-fill',
    };

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi ${iconMap[type] || iconMap.info} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/**
 * Gibt einen Auftrag frei (POST /api/orders/{id}/start).
 */
async function startOrder(orderId) {
    if (!confirm(`Auftrag #${orderId} wirklich freigeben?`)) return;

    try {
        const res = await fetch(`/api/orders/${orderId}/start`, { method: 'POST' });
        const data = await res.json();

        if (res.ok && data.success) {
            showToast(data.message, 'success');
            // Badge aktualisieren
            const row = document.getElementById(`order-row-${orderId}`);
            if (row) {
                const badge = row.querySelector('td:nth-last-child(2) .badge');
                if (badge) {
                    badge.className = 'badge bg-info';
                    badge.textContent = 'Validiert';
                }
            }
        } else {
            showToast(data.error || 'Fehler beim Freigeben', 'danger');
        }
    } catch (err) {
        showToast('Netzwerkfehler: ' + err.message, 'danger');
    }
}

/**
 * Loescht einen Auftrag (DELETE /api/orders/{id}).
 */
async function deleteOrder(orderId) {
    if (!confirm(`Auftrag #${orderId} wirklich loeschen? Diese Aktion kann nicht rueckgaengig gemacht werden.`)) return;

    try {
        const res = await fetch(`/api/orders/${orderId}`, { method: 'DELETE' });
        const data = await res.json();

        if (res.ok && data.success) {
            showToast(data.message, 'success');
            // Zeile ausblenden
            const row = document.getElementById(`order-row-${orderId}`);
            if (row) {
                row.style.transition = 'opacity 0.3s';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 300);
            }
        } else {
            showToast(data.error || 'Fehler beim Loeschen', 'danger');
        }
    } catch (err) {
        showToast('Netzwerkfehler: ' + err.message, 'danger');
    }
}
