export interface ChatResponse {
  /** Session identifier */
  session_id: string;
  /** Agent response message */
  response: string;
  /** Current session state */
  session_state: SessionState;
  /** Suggested next actions for the user */
  next_actions: string[];
}

export type SessionState = 'initial' | 'tracking' | 'advised' | 'completed';
