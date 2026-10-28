# ==============================================================================
# Service 2: Web Gateway & Reverse Proxy (Nginx on Alpine Linux)
# Base Image: nginx:1.27-alpine (Ultra-lightweight ~23MB footprint)
# ==============================================================================
FROM nginx:1.27-alpine

# Remove default welcome configuration
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static web testing dashboard assets
COPY static/ /usr/share/nginx/html/

# Expose HTTP port 80
EXPOSE 80

# Healthcheck to verify proxy is serving traffic
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

# Launch Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
