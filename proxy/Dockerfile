FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="django_rest_apis.com"

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app_deploy
ENV APP_PORT=8085

USER root

RUN mkdir -p /static_files && \
    chmod 755 /static_files && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

VOLUME /static_files

USER nginx

CMD ["sh", "/run.sh"]