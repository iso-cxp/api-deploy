FROM node:alpine

ADD . /var/www/terminal

WORKDIR /var/www/terminal

RUN npm install

EXPOSE 3000

CMD [ "npm", "start" ]
