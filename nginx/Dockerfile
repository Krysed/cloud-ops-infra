FROM nginx:1.28.0-alpine-slim

COPY conf.d/app.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
