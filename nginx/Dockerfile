FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf

COPY conf.d/app.conf /etc/nginx/conf.d/app.conf

HEALTHCHECK --interval=30s --timeout=3s CMD nc -z localhost 80 || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
