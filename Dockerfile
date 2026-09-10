FROM python:3.13-alpine AS build
WORKDIR /site
COPY scripts/build.py scripts/build.py
COPY source source
COPY public public
RUN python3 scripts/build.py

FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site/dist /usr/share/nginx/html
EXPOSE 80
