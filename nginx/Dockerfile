FROM nginx

COPY ./static /usr/share/nginx/html
COPY ./nginx/nginx.conf.tmp /etc/nginx/nginx.conf.tmp

CMD envsubst '${API_ROUTE}'< /etc/nginx/nginx.conf.tmp > /etc/nginx/nginx.conf && nginx -g "daemon off;"
