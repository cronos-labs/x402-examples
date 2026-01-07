FROM node:20

WORKDIR /usr/src/app

RUN npm install -g typescript nodemon

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 5000

CMD ["sh", "-c", "node ./dist"]
