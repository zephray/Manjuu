# Manjū VSCode Plugin Readme

- File Extension: .pyv
- [x] Basic PyHP Syntax Highlighting
- [ ] Manjuu Snippets
- [ ] Examples

Note: 

Lines like this will not work because the python syntax is expected to capture everything until line break. The embedded python has a higher priority than the pyv syntax.

```
    <% from manjuu import * %>
``` 
Instead, we need to add a line break
``` 
    <% from manjuu import *
    %>
``` 
or
```
    <% 
        from manjuu import *
    %>
```