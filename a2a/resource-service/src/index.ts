import cors from 'cors';
import express from 'express';
import * as routes from './routes/index.js';

const app = express();
const port = process.env.PORT || 8787;

app.use(cors());

routes.register(app);

const startServer = async () => {
  app.listen(port, () => {
    console.info(`Running on port ${port}`);
  });
};

startServer();
