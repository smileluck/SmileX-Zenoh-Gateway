***

## add-apache-license-header

# Add License Header

This skill automatically adds Apache License 2.0 copyright header to source code files.

## When to Invoke

**Trigger Conditions:**

- User creates a new source code file
- User asks to add license header to existing files
- Before finalizing a new file in the repository

## Supported File Types

| Language              | Extensions                   | Header Pattern                  |
| --------------------- | ---------------------------- | ------------------------------- |
| Python                | `.py`                        | `# `  comment style             |
| JavaScript/TypeScript | `.js`, `.ts`, `.jsx`, `.tsx` | `// `  comment style            |
| Java                  | `.java`                      | `// `  comment style            |
| C/C++                 | `.c`, `.cpp`, `.h`, `.hpp`   | `// `  or `/* */` comment style |
| Go                    | `.go`                        | `// `  comment style            |
| Rust                  | `.rs`                        | `// `  comment style            |
| Shell                 | `.sh`                        | `# `  comment style             |
| YAML                  | `.yaml`, `.yml`              | `# `  comment style             |
| JSON                  | `.json`                      | (no comments, skip)             |
| Markdown              | `.md`                        | (no code header needed)         |

## License Header Template

```python
# Copyright 2026 SmileX
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

## Usage

### When Creating New Files

When you create a new source code file, immediately add the appropriate license header at the top of the file.

**Python Example:**

```python
# Copyright 2026 SmileX
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def main():
    pass
```

**JavaScript Example:**

```javascript
// Copyright 2026 SmileX
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function main() {
}
```

### For Existing Files

If user asks to add license header to existing files:

1. Read the file content
2. Prepend the appropriate license header
3. Write the file back

## Important Notes

- **Do NOT add headers to**: `LICENSE`, `.gitignore`, `.md` files, binary files, or configuration files that don't support comments
- Always use the exact header template provided above
- Maintain consistent comment style for each file type
- Keep the blank line after the header before the actual code

