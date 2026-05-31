import { ModelData } from '../types/models';

// Metrics calculated with k=1
export const modelData: ModelData[] = [
  {
    "model": "claude-3-opus-20240229",
    "pass@k": 66.67,
    "secure@k_pass": 66.67,
    "secure_pass@k": 100.0,
    "rank": 1,
    "type": "Proprietary"
  },
  {
    "model": "claude-opus-4-1-20250805",
    "pass@k": 66.67,
    "secure@k_pass": 66.67,
    "secure_pass@k": 100.0,
    "rank": 2,
    "type": "Proprietary"
  },
  {
    "model": "claude-opus-4-20250514",
    "pass@k": 33.33,
    "secure@k_pass": 33.33,
    "secure_pass@k": 100.0,
    "rank": 3,
    "type": "Proprietary"
  },
  {
    "model": "claude-3-5-sonnet-20241022",
    "pass@k": 0.0,
    "secure@k_pass": 0.0,
    "secure_pass@k": 0,
    "rank": 4,
    "type": "Proprietary"
  },
  {
    "model": "claude-3-haiku-20240307",
    "pass@k": 0.0,
    "secure@k_pass": 0.0,
    "secure_pass@k": 0,
    "rank": 5,
    "type": "Proprietary"
  },
  {
    "model": "claude-sonnet-4-20250514",
    "pass@k": 0.0,
    "secure@k_pass": 0.0,
    "secure_pass@k": 0,
    "rank": 6,
    "type": "Proprietary"
  },
  {
    "model": "gemini",
    "pass@k": 0.0,
    "secure@k_pass": 0.0,
    "secure_pass@k": 0,
    "rank": 7,
    "type": "Proprietary"
  },
  {
    "model": "gemini-2.0-flash",
    "pass@k": 0.0,
    "secure@k_pass": 0.0,
    "secure_pass@k": 0,
    "rank": 8,
    "type": "Proprietary"
  },
  {
    "model": "claude-3-7-sonnet-20250219",
    "pass@k": 0.0,
    "secure@k_pass": 0.0,
    "secure_pass@k": 0,
    "rank": 9,
    "type": "Proprietary"
  }
];