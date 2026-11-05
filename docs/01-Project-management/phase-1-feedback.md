# How the Phase 1 feedback was addressed

Tutor feedback received on 27 Jul 2026. Each point and where it is resolved:

| # | Feedback | Resolution | Where |
|---|---|---|---|
| 1 | The project plan should reflect the agile approach: work packages, time estimates. | Scrum roles, events and Definition of Done; product backlog with user stories and story points; 12 work packages with hour estimates; one-week sprints with goals and dates; burndown table. | [project-plan.md](project-plan.md) |
| 2 | Non-functional requirements need concrete target values. | Every NFR has a measurable target and a verification method. | [requirements.md §3](../02-Requirements/requirements.md#3-non-functional-requirements) |
| 3 | Requirements and proposed solutions are mixed. | Requirements state *what* the system does; implementation choices (bcrypt, JWT, cache duration, Docker) moved to architecture decisions. | [requirements.md](../02-Requirements/requirements.md), [ADRs](../03-Architecture-documentation/adr/) |
| 4 | The component diagram should use a standard notation such as UML. | UML 2 component diagram with components, provided/required interfaces and dependencies. | [component-diagram.puml](../03-Architecture-documentation/diagrams/component-diagram.puml) |
| 5 | Briefly explain why this technology stack and not an alternative. | Each technology is compared with named alternatives, with the reason for the choice. | [tech-stack.md](../03-Architecture-documentation/tech-stack.md), [ADR-0001](../03-Architecture-documentation/adr/0001-technology-stack.md) |
| 6 | Specify exact test cases with input values and expected behaviour. | Test-case catalogue with ID, requirement, input, expected result and the automated test that runs it. | [test-cases.md](../02-Requirements/test-cases.md) |
| 7 | The glossary must be sorted alphabetically. | Glossary sorted A–Z and extended. | [glossary.md](../02-Requirements/glossary.md) |

The title page date of the Phase 1 document ("24th July, 2027") is corrected to 24 July 2026 in
the revised version.
