FROM nginx:1.28.0-alpine-slim

COPY ./static/ /usr/share/nginx/html/static/
COPY ./template/ /usr/share/nginx/html/
COPY wait_for_backend.sh .
COPY ./conf.d/nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    apk add --no-cache netcat-openbsd

EXPOSE 80

ENTRYPOINT ["/wait_for_backend.sh"]
CMD ["nginx", "-g", "daemon off;"]
