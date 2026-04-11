import { z } from "zod";

export const ZResearchStatus = z.enum([
  "queued",
  "running",
  "completed",
  "failed",
  "partial",
]);

export const ZResearchRequest = z.object({
  query: z.string().min(10).max(500),
  session_id: z.string().uuid().optional(),
});

export const ZReportSection = z.object({
  heading: z.string(),
  content: z.string(),
  citations: z.array(z.string()),
});

export const ZReportSource = z.object({
  title: z.string(),
  url: z.string().url(),
  source_type: z.enum(["web", "pdf", "internal_doc"]),
});

export const ZReportConfidence = z.object({
  overall: z.number().min(0).max(1),
  data_quality: z.number().min(0).max(1),
  source_reliability: z.number().min(0).max(1),
});

export const ZResearchEvent = z.object({
  type: z.string(),
  status: ZResearchStatus,
  message: z.string(),
  agent: z.string().optional(),
  timestamp: z.string().datetime(),
  data: z.record(z.string(), z.any()).optional(),
});

export const ZResearchReport = z.object({
  title: z.string(),
  summary: z.string(),
  sections: z.array(ZReportSection),
  sources: z.array(ZReportSource),
  confidence: ZReportConfidence,
});

export const ZResearchCreatedResponse = z.object({
  session_id: z.string().uuid(),
  status: ZResearchStatus,
  stream_url: z.string(),
});

export const ZResearchSessionResponse = z.object({
  session_id: z.string().uuid(),
  query: z.string(),
  status: ZResearchStatus,
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  started_at: z.string().datetime().optional(),
  completed_at: z.string().datetime().optional(),
  report: ZResearchReport.optional(),
  events: z.array(ZResearchEvent).optional(),
  error: z.string().optional(),
});
