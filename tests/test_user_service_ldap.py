"""Tests für den UserService mit LDAP."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from skriptendruck.models import User
from skriptendruck.services import UserService


class TestUserServiceLDAP:
    """Tests für LDAP-Funktionalität im UserService."""
    
    def setup_method(self) -> None:
        """Setup für jeden Test."""
        self.service = UserService()
    
    @patch('skriptendruck.services.user_service.settings')
    @patch('skriptendruck.services.user_service.Connection')
    @patch('skriptendruck.services.user_service.Server')
    def test_ldap_query_success(self, mock_server, mock_connection, mock_settings) -> None:
        """Test: Erfolgreiche LDAP-Abfrage."""
        # Settings mocken
        mock_settings.ldap_enabled = True
        mock_settings.ldap_server = "ldap://test.example.com"
        mock_settings.ldap_base_dn = "ou=people,dc=example,dc=com"
        mock_settings.ldap_bind_dn = None
        mock_settings.ldap_bind_password = None
        
        # LDAP Entry mocken
        mock_entry = MagicMock()
        mock_entry.givenName.value = "Max"
        mock_entry.sn.value = "Mustermann"
        mock_entry.mail.value = "max.mustermann@example.com"
        mock_entry.ou.value = "Maschinenbau"
        
        # Connection mocken
        mock_conn_instance = MagicMock()
        mock_conn_instance.entries = [mock_entry]
        mock_connection.return_value = mock_conn_instance
        
        # Test
        user = self.service._query_ldap("mus12345")
        
        assert user is not None
        assert user.username == "mus12345"
        assert user.first_name == "Max"
        assert user.last_name == "Mustermann"
        assert user.email == "max.mustermann@example.com"
        assert user.faculty == "M"
        
        # Verify LDAP calls
        mock_connection.assert_called_once()
        mock_conn_instance.search.assert_called_once()
        mock_conn_instance.unbind.assert_called_once()
    
    @patch('skriptendruck.services.user_service.settings')
    @patch('skriptendruck.services.user_service.Connection')
    @patch('skriptendruck.services.user_service.Server')
    def test_ldap_query_with_authentication(
        self, mock_server, mock_connection, mock_settings
    ) -> None:
        """Test: LDAP-Abfrage mit Authentifizierung."""
        # Settings mit Credentials mocken
        mock_settings.ldap_enabled = True
        mock_settings.ldap_server = "ldap://test.example.com"
        mock_settings.ldap_base_dn = "ou=people,dc=example,dc=com"
        mock_settings.ldap_bind_dn = "cn=admin,dc=example,dc=com"
        mock_settings.ldap_bind_password = "secret"
        
        # LDAP Entry mocken
        mock_entry = MagicMock()
        mock_entry.givenName.value = "Lisa"
        mock_entry.sn.value = "Schmidt"
        mock_entry.mail.value = "lisa.schmidt@example.com"
        mock_entry.ou.value = "Informatik"
        
        # Connection mocken
        mock_conn_instance = MagicMock()
        mock_conn_instance.entries = [mock_entry]
        mock_connection.return_value = mock_conn_instance
        
        # Test
        user = self.service._query_ldap("sch12345")
        
        assert user is not None
        assert user.username == "sch12345"
        assert user.faculty == "I"
        
        # Verify authentication was used
        mock_connection.assert_called_once()
        call_kwargs = mock_connection.call_args[1]
        assert call_kwargs['user'] == "cn=admin,dc=example,dc=com"
        assert call_kwargs['password'] == "secret"
    
    @patch('skriptendruck.services.user_service.settings')
    @patch('skriptendruck.services.user_service.Connection')
    @patch('skriptendruck.services.user_service.Server')
    def test_ldap_query_user_not_found(
        self, mock_server, mock_connection, mock_settings
    ) -> None:
        """Test: LDAP-Abfrage wenn Benutzer nicht gefunden."""
        # Settings mocken
        mock_settings.ldap_enabled = True
        mock_settings.ldap_server = "ldap://test.example.com"
        mock_settings.ldap_base_dn = "ou=people,dc=example,dc=com"
        mock_settings.ldap_bind_dn = None
        mock_settings.ldap_bind_password = None
        
        # Connection mocken - keine Einträge
        mock_conn_instance = MagicMock()
        mock_conn_instance.entries = []
        mock_connection.return_value = mock_conn_instance
        
        # Test
        user = self.service._query_ldap("nonexistent")
        
        assert user is None
    
    @patch('skriptendruck.services.user_service.settings')
    def test_ldap_query_not_configured(self, mock_settings) -> None:
        """Test: LDAP-Abfrage ohne Konfiguration."""
        # Settings ohne LDAP-Konfiguration
        mock_settings.ldap_enabled = True
        mock_settings.ldap_server = None
        mock_settings.ldap_base_dn = None
        
        # Test
        user = self.service._query_ldap("test")
        
        assert user is None
    
    @patch('skriptendruck.services.user_service.settings')
    @patch('skriptendruck.services.user_service.Connection')
    @patch('skriptendruck.services.user_service.Server')
    def test_ldap_query_connection_error(
        self, mock_server, mock_connection, mock_settings
    ) -> None:
        """Test: LDAP-Abfrage mit Verbindungsfehler."""
        # Settings mocken
        mock_settings.ldap_enabled = True
        mock_settings.ldap_server = "ldap://test.example.com"
        mock_settings.ldap_base_dn = "ou=people,dc=example,dc=com"
        
        # Connection wirft Fehler
        mock_connection.side_effect = Exception("Connection failed")
        
        # Test
        user = self.service._query_ldap("test")
        
        assert user is None
    
    @patch('skriptendruck.services.user_service.settings')
    @patch('skriptendruck.services.user_service.Connection')
    @patch('skriptendruck.services.user_service.Server')
    def test_ldap_query_with_list_attributes(
        self, mock_server, mock_connection, mock_settings
    ) -> None:
        """Test: LDAP-Abfrage wenn Attribute als Liste zurückgegeben werden."""
        # Settings mocken
        mock_settings.ldap_enabled = True
        mock_settings.ldap_server = "ldap://test.example.com"
        mock_settings.ldap_base_dn = "ou=people,dc=example,dc=com"
        mock_settings.ldap_bind_dn = None
        mock_settings.ldap_bind_password = None
        
        # LDAP Entry mit Listen-Attributen mocken
        mock_entry = MagicMock()
        mock_entry.givenName.value = ["Max", "Maximilian"]  # Liste
        mock_entry.sn.value = ["Mustermann"]  # Liste
        mock_entry.mail.value = ["max@example.com", "max.m@example.com"]  # Liste
        mock_entry.ou.value = ["Maschinenbau"]  # Liste
        
        # Connection mocken
        mock_conn_instance = MagicMock()
        mock_conn_instance.entries = [mock_entry]
        mock_connection.return_value = mock_conn_instance
        
        # Test
        user = self.service._query_ldap("mus12345")
        
        assert user is not None
        assert user.first_name == "Max"  # Erster Wert der Liste
        assert user.last_name == "Mustermann"  # Erster Wert der Liste
        assert user.email == "max@example.com"  # Erster Wert der Liste
    
    def test_get_user_with_ldap_enabled(self) -> None:
        """Test: get_user nutzt LDAP wenn aktiviert."""
        with patch.object(self.service, '_query_ldap') as mock_query:
            mock_user = User(
                username="test123",
                first_name="Test",
                last_name="User",
                faculty="M"
            )
            mock_query.return_value = mock_user
            
            with patch('skriptendruck.services.user_service.settings') as mock_settings:
                mock_settings.ldap_enabled = True
                
                user = self.service.get_user("test123")
                
                assert user is not None
                assert user.username == "test123"
                mock_query.assert_called_once_with("test123")
    
    def test_get_user_blacklist_check(self) -> None:
        """Test: get_user prüft Blacklist nach LDAP-Abfrage."""
        # Blacklist vorbereiten
        self.service._blacklist.add("blocked123")
        
        with patch.object(self.service, '_query_ldap') as mock_query:
            mock_user = User(
                username="blocked123",
                first_name="Blocked",
                last_name="User",
                faculty="M"
            )
            mock_query.return_value = mock_user
            
            with patch('skriptendruck.services.user_service.settings') as mock_settings:
                mock_settings.ldap_enabled = True
                
                user = self.service.get_user("blocked123")
                
                assert user is not None
                assert user.is_blocked is True
    
    def test_faculty_code_mapping(self) -> None:
        """Test: Fakultätsnamen werden korrekt zu Codes gemappt."""
        test_cases = [
            ("Maschinenbau", "M"),
            ("Elektrotechnik", "E"),
            ("Informatik", "I"),
            ("Bauingenieurwesen", "B"),
            ("Architektur", "A"),
            ("Betriebswirtschaft", "BW"),
            ("Unknown Faculty", "U"),  # Fallback: Erster Buchstabe
            ("", "?"),  # Leerer String
        ]
        
        for faculty_name, expected_code in test_cases:
            result = self.service._get_faculty_code(faculty_name)
            assert result == expected_code, f"Failed for {faculty_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
