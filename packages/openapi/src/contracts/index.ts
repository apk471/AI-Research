import { initContract } from "@ts-rest/core";
import { healthContract } from "./health.js";
import { researchContract } from "./research.js";

const c = initContract();

export const apiContract = c.router({
  Health: healthContract,
  Research: researchContract,
});
