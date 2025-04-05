FROM nginx:alpine

COPY ./conf.d/nginx.conf /etc/nginx/conf.d/default.conf
COPY ./static/ /usr/share/nginx/html/static/
COPY ./template/ /usr/share/nginx/html/

RUN mkdir -p /usr/share/nginx/html/static && \
chown -R nginx:nginx /usr/share/nginx/html && \
chmod -R 755 /usr/share/nginx/html

HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -q -O /dev/null http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]