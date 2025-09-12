window.ENV = window.ENV || {};
// Usar mesmo domínio/porta com reverse proxy do Nginx (ver nginx.conf)
window.ENV.API_BASE_URL = window.ENV.API_BASE_URL || '/api';
