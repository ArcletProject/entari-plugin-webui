declare module "*.css?inline" {
  const content: string;
  export default content;
}

declare module "*?worker" {
  const WorkerFactory: new () => Worker;
  export default WorkerFactory;
}
