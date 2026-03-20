FROM node:20-slim AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN rm -f /etc/nginx/templates/default.conf.template /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.d/15-railway-resolvers.sh /docker-entrypoint.d/15-railway-resolvers.sh
RUN chmod +x /docker-entrypoint.d/15-railway-resolvers.sh
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
