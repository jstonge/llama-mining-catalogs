
# Welcome
_"How can we use LLMS to mine data". This is our big question. We run experiments to assess time and efforts of different approaches to solve that problem._

## Project structure

We take as starting point the observable framework structure, but modify it a little to accomodate our data processing pipeline. That is, on top of the Framework project that mostly lives in `docs/` (see hidden summary below for authors' description), we have a project structure heavily inspired from the [Turing Way's repository structure](https://book.the-turing-way.org/project-design/project-repo/project-repo-advanced#example-with-every-possible-folder):

```ini
.
├─ data # Observable framework app
│  ├─ clean       # processed file
│  │  └─ train/test/validation
│  └─ raw       
├─ docs # Observable framework app (see <details>)
├─ src
|  ├─ moving_annots # scripts to move around anots
│  │  ├─ catDB_to_BBA.py
│  │  ├─ ...
│  │  └─ cNER_to_cSFT.py
│  ├─ kfold_split.py 
│  ├─ prepare_fpNER_annots.py 
│  └─ helpers.py  # helpers shared across scripts
├─ static  # static resources (images and audio files)
├─ Makefile # A makefile to run the pipeline
├── report/   # static analysis
│   └── report.tex
├─ README.md
└─ reqirements.txt
```


<details><summary>How to get started with Observable Framework</summary>


This is an [Observable Framework](https://observablehq.com/framework) project. To start the local preview server, run:

```
npm run dev
```

Then visit <http://localhost:3000> to preview your project.

For more, see <https://observablehq.com/framework/getting-started>.

## Project structure

A typical Framework project looks like this:

```ini
.
├─ docs
│  ├─ components
│  │  └─ timeline.js           # an importable module
│  ├─ data
│  │  ├─ launches.csv.js       # a data loader
│  │  └─ events.json           # a static data file
│  ├─ example-dashboard.md     # a page
│  ├─ example-report.md        # another page
│  └─ index.md                 # the home page
├─ .gitignore
├─ observablehq.config.js      # the project config file
├─ package.json
└─ README.md
```

**`docs`** - This is the “source root” — where your source files live. Pages go here. Each page is a Markdown file. Observable Framework uses [file-based routing](https://observablehq.com/framework/routing), which means that the name of the file controls where the page is served. You can create as many pages as you like. Use folders to organize your pages.

**`docs/index.md`** - This is the home page for your site. You can have as many additional pages as you’d like, but you should always have a home page, too.

**`docs/data`** - You can put [data loaders](https://observablehq.com/framework/loaders) or static data files anywhere in your source root, but we recommend putting them here.

**`docs/components`** - You can put shared [JavaScript modules](https://observablehq.com/framework/javascript/imports) anywhere in your source root, but we recommend putting them here. This helps you pull code out of Markdown files and into JavaScript modules, making it easier to reuse code across pages, write tests and run linters, and even share code with vanilla web applications.

**`observablehq.config.js`** - This is the [project configuration](https://observablehq.com/framework/config) file, such as the pages and sections in the sidebar navigation, and the project’s title.

## Command reference

| Command           | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `npm install`            | Install or reinstall dependencies                        |
| `npm run dev`        | Start local preview server                               |
| `npm run build`      | Build your static site, generating `./dist`              |
| `npm run deploy`     | Deploy your project to Observable                        |
| `npm run clean`      | Clear the local data loader cache                        |
| `npm run observable` | Run commands like `observable help`                      |

</details>
