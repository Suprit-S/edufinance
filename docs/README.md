# EduFinance – Project Documentation

The structure mirrors the submission folder required by the assignment (chapter 4.2).

| Folder | Contents |
|---|---|
| [01-Project-management](01-Project-management/) | [Project plan](01-Project-management/project-plan.md) (Scrum, backlog, work packages, sprints), [sprint notes](01-Project-management/sprint-notes.md), [change requests](01-Project-management/change-requests.md), [Phase 1 feedback resolution](01-Project-management/phase-1-feedback.md) |
| [02-Requirements](02-Requirements/) | [Requirements](02-Requirements/requirements.md) (FR, NFR, user stories), [glossary](02-Requirements/glossary.md), [test cases](02-Requirements/test-cases.md), [traceability](02-Requirements/traceability.md) |
| [03-Architecture-documentation](03-Architecture-documentation/) | [Architecture (arc42)](03-Architecture-documentation/architecture.md), [tech stack](03-Architecture-documentation/tech-stack.md), [ADRs](03-Architecture-documentation/adr/README.md), [UML diagrams](03-Architecture-documentation/diagrams/) |
| [technical-debt.md](technical-debt.md) | Known limitations |

**Regenerating diagram images** (requires Java and Graphviz):

```bash
cd docs/03-Architecture-documentation/diagrams
java -jar plantuml.jar -tpng -o png *.puml
```

Or paste a `.puml` file into <https://www.plantuml.com/plantuml>.
