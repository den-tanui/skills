## Overview

Zod integrates with React Hook Form.

## Patterns

```typescript
const schema = z.object({ email: z.string().email() });
```