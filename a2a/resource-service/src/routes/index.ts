import * as express from 'express';
import bodyParser from 'body-parser';

import resourceRouter from './resource.routes.js';
import discoverRouter from './well-known.routes.js';

/**
 * Registers application-wide middleware and routes.
 *
 * Responsibilities:
 * - Configure request body parsing.
 * - Mount API routers under their base paths.
 *
 * @remarks
 * This function mutates the provided Express application instance.
 * Middleware is registered in the order defined here.
 *
 * @param app - Express application instance to configure.
 */
export const register = (app: express.Application): void => {
  /**
   * Parses incoming request bodies as JSON using `body-parser`.
   *
   * @remarks
   * This is functionally redundant with `express.json()` for most use cases,
   * but is kept here for compatibility or legacy reasons.
   */
  app.use(bodyParser.json());

  /**
   * Parses incoming request bodies as JSON using Express built-in middleware.
   */
  app.use(express.json());

  /**
   * Mounts all resource-related routes under the `/api` path prefix.
   */
  app.use('/api', resourceRouter);

  /**
   * Well-known discovery routes (A2A Agent Card).
   *
   * Mounted at `/.well-known` by route registration.
   */
  app.use('/.well-known', discoverRouter);
};
