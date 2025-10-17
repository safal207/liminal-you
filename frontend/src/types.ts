export type Reflection = {
  id: string;
  author: string;
  content: string;
  emotion: string;
  pad?: [number, number, number];
};

export type ReflectionPayload = {
  from_node: string;
  to_user: string;
  message: string;
  emotion: string;
  pad?: [number, number, number];
};

export type Profile = {
  id: string;
  name: string;
  bio?: string;
  nodes: { id: string; label: string }[];
  reflections_count: number;
  emotions: Record<string, number>;
  astro_opt_out: boolean;
};
