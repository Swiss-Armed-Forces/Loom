const MIME_TO_MODE_MAP: { [key: string]: string } = {
    // Web Technologies
    "text/html": "html",
    "application/xhtml+xml": "html",
    "text/css": "css",
    "text/sass": "sass",
    "text/scss": "scss",
    "text/less": "less",
    "text/stylus": "stylus",

    // JavaScript & TypeScript
    "text/javascript": "javascript",
    "application/javascript": "javascript",
    "application/x-javascript": "javascript",
    "text/typescript": "typescript",
    "application/typescript": "typescript",
    "text/jsx": "jsx",
    "text/tsx": "tsx",
    "application/json": "json",
    "application/ld+json": "json",
    "text/json": "json",

    // Programming Languages
    "text/x-python": "python",
    "application/x-python-code": "python",
    "text/x-java-source": "java",
    "text/x-java": "java",
    "text/x-c": "c_cpp",
    "text/x-c++src": "c_cpp",
    "text/x-c++": "c_cpp",
    "text/x-csharp": "csharp",
    "text/x-php": "php",
    "application/x-php": "php",
    "text/x-ruby": "ruby",
    "application/x-ruby": "ruby",
    "text/x-go": "golang",
    "text/x-rust": "rust",
    "text/x-kotlin": "kotlin",
    "text/x-scala": "scala",
    "text/x-swift": "swift",
    "text/x-objectivec": "objectivec",

    // Functional Languages
    "text/x-haskell": "haskell",
    "text/x-erlang": "erlang",
    "text/x-elixir": "elixir",
    "text/x-clojure": "clojure",
    "text/x-fsharp": "fsharp",
    "text/x-ocaml": "ocaml",
    "text/x-scheme": "scheme",
    "text/x-lisp": "lisp",

    // Shell & Config
    "text/x-shellscript": "sh",
    "application/x-sh": "sh",
    "text/x-bash": "sh",
    "text/x-zsh": "sh",
    "text/x-fish": "sh",
    "text/x-powershell": "powershell",
    "text/x-dockerfile": "dockerfile",
    "text/x-makefile": "makefile",
    "text/x-cmake": "cmake",

    // Markup & Documentation
    "text/xml": "xml",
    "application/xml": "xml",
    "text/markdown": "markdown",
    "text/x-markdown": "markdown",
    "application/x-tex": "latex",
    "text/x-tex": "latex",
    "text/x-rst": "rst",
    "text/x-asciidoc": "asciidoc",

    // Data Formats
    "text/yaml": "yaml",
    "application/x-yaml": "yaml",
    "text/x-yaml": "yaml",
    "text/x-toml": "toml",
    "text/csv": "text",
    "text/tab-separated-values": "text",
    "application/x-ini": "ini",
    "text/x-properties": "properties",

    // Database
    "application/sql": "mysql",
    "text/x-sql": "mysql",
    "text/x-mysql": "mysql",
    "text/x-postgresql": "pgsql",
    "text/x-plsql": "plsql",
    "text/x-cassandra": "cassandra",

    // Web Assembly & Low Level
    "text/x-assembly": "assembly_x86",
    "application/wasm": "wasm",

    // Templating
    "text/x-handlebars": "handlebars",
    "text/x-mustache": "mustache",
    "text/x-twig": "twig",
    "text/x-smarty": "smarty",
    "text/x-velocity": "velocity",
    "text/x-freemarker": "ftl",

    // Game Development
    "text/x-lua": "lua",
    "text/x-glsl": "glsl",
    "text/x-hlsl": "hlsl",

    // Mobile Development
    "text/x-dart": "dart",

    // Scientific Computing
    "text/x-r": "r",
    "text/x-matlab": "matlab",
    "text/x-octave": "matlab",
    "text/x-julia": "julia",

    // Legacy & Specialized
    "text/x-perl": "perl",
    "text/x-tcl": "tcl",
    "text/x-pascal": "pascal",
    "text/x-fortran": "fortran",
    "text/x-cobol": "cobol",
    "text/x-ada": "ada",
    "text/x-vbscript": "vbscript",
    "text/x-vb": "vbscript",
    "text/x-actionscript": "actionscript",

    // Configuration Files
    "text/x-apache-conf": "apache_conf",
    "text/x-nginx-conf": "nginx",
    "text/x-gitignore": "gitignore",
    "text/x-editorconfig": "editorconfig",

    // Default
    "text/plain": "text",
    "application/octet-stream": "text",
};

export const inferAceModeFromMimeType = (mimeType: string | undefined) => {
    if (!mimeType) return "text";
    return MIME_TO_MODE_MAP[mimeType] ?? "text";
};
