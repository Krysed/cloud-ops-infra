FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf

COPY conf.d/app.conf /etc/nginx/conf.d/app.conf
RUN mkdir -p /var/www/static /var/www/template && \
    chown -R nginx:nginx /var/www

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
