First study the documents in spec/ref/ to understand my project's design and API.

Create four HTML files in var/: sync_facade.html, sync_uni.html, async_facade.html,
async_uni.html. In each document there must be usage examples for 2captcha
(https://github.com/2captcha/2captcha-python) and for my project. Two columns in
each document: in the left column are 2captcha code
examples, in the right column similar code but using my library.

- The facade files show my library's facade interface; the uni files show my
  library's universal interface.
- The sync files use the synchronous clients of both libraries; the async files
  use the asynchronous ones.
- Generate all possible examples: every challenge type my library supports
  (including a with-proxy variant), plus account balance and reporting a bad
  result. If a 2captcha example is about a challenge type which is not supported
  by my library yet, do not show such example. Skip 2captcha's manual submit/poll
  flow too.
- Each example is a pair: a centered header with the example name, then the two
  columns with code. Do not put labels before each code box.
- The main page header must be centered, with spacing after it and after each
  pair header. Pair headers must be as big as the main header.
- At the very top of each file add a row with links to all these 4 files; the
  current link must be bold.
- Use plain monospace styling. Do syntax highlighting client-side with a
  JavaScript library that auto-highlights code (no pre-rendered highlighting
  such as pygments), using an appropriate light theme: white or very light
  background for code blocks, not a dark one. Load the highlighting library
  and its theme from a CDN.
- Under the right column you may add a short note explaining my library's side.

My library is not implemented yet, so its code examples must follow the API from
the project docs.

When the four HTML files are done, stop. Do not create report files or commits.
