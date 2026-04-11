import { initContract } from "@ts-rest/core";
import {
  ZResearchCreatedResponse,
  ZResearchRequest,
  ZResearchSessionResponse,
} from "@boilerplate/zod";

const c = initContract();

export const researchContract = c.router({
  createResearch: {
    summary: "Create research session",
    path: "/api/v1/research",
    method: "POST",
    body: ZResearchRequest,
    responses: {
      202: ZResearchCreatedResponse,
    },
  },
  getResearchSession: {
    summary: "Get research session",
    path: "/api/v1/research/:sessionId",
    method: "GET",
    pathParams: c.type<{ sessionId: string }>(),
    responses: {
      200: ZResearchSessionResponse,
    },
  },
});
