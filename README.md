# Conceivable — engineering case study

I spent 25 years as a reproductive acupuncturist, reading the cycles of more than ten thousand women. Conceivable is that clinical practice rebuilt as software: an AI coach that runs a real interview, figures out what's actually off, and builds a plan around it.

This repository is a public case study. The product code is private — Conceivable is a live health product with real users — so what's here is the architecture, the decisions, the tradeoffs I got right and wrong, and one real subsystem extracted in full.

---

## The problem

Fertility advice is delivered as a list. Eat well, sleep more, take a prenatal, track your cycle, reduce stress. The list is not wrong; it's just population-level. It tells a woman what helps on average, and then she tries to do all of it, perfectly, forever — and the anxiety of maintaining that becomes its own problem.

The clinical insight the product is built on: **her own signals tell you which two or three items on that list are actually hers.** A scanty bleed points somewhere specific. A short luteal phase points somewhere else. An afternoon energy crash is a blood-sugar conversation before it is a supplement conversation. The signal picks the intervention.

Software is unusually good at that job — reading signals over time and narrowing a generic list to a specific plan. That's the whole product thesis.

---

## System shape

Four surfaces, one brain.

**iOS app** — Next.js rendered inside a Capacitor shell, shipped through TestFlight to the App Store. Voice-first daily check-in, cycle and basal body temperature tracking, a personalized daily plan, and a toolbox (breathwork, acupressure, guided audio) for the days that are hard rather than tactical.

**Kai, the coach** — a structured clinical interview rather than a chat toy. It gathers the same signals I gathered in clinic, reasons toward root cause, and produces a plan. Every recommendation is rail-guarded: it can only select from a known formulary, and combinations are validated against clinical safety rules before a customer ever sees them.

**Storefront** — Shopify, with a custom pack-builder experience wired to a fulfillment partner's API. Personalized supplement packs arrive as daily pouches instead of a shelf of bottles.

**Command Center** — the internal operations platform. Marketing automation, funnel analytics, content pipelines, and the daily numbers that actually run the company.

---

## Decisions worth defending

**Boring tools on purpose.** I optimize for "still works in six months when I've forgotten how it works." That has meant choosing the well-understood option repeatedly, and being suspicious of cleverness that only I can maintain.

**One codebase, many lenses.** A woman's needs change — trying to conceive, pregnant, postpartum, perimenopausal. Rather than separate apps, the product is one base with lenses layered over it, and an explicit transition engine that owns the handoff when someone's life stage changes. There is exactly one entry point into that transition, because when I allowed several, state drifted and users landed in a half-migrated app.

**The AI is railed, not free.** A general model given free rein over health guidance is a liability. Recommendations come from a fixed formulary, run through a validation step that can block a combination outright, and clinical claims require a citation or they don't ship. The interesting engineering is in the constraints, not the generation.

**Native storage, not browser storage.** An early version tracked onboarding state in web storage inside the native shell. iOS evicts that whenever it likes, so users were silently thrown back to the first screen. The fix — native storage plus a real sign-in path — is unglamorous and was the single largest retention bug I've fixed.

**Verify on production, not on green tests.** Health products fail quietly. Every deploy is checked against the live surface afterward, and "it built successfully" is not evidence that it works.

---

## Things I got wrong

Worth more than the wins, in my experience.

**I shipped a paywall that could trap someone.** A trial that auto-converted to an annual plan with no visible way out is a bad experience regardless of what it does to conversion. Rebuilt as a plan choice plus an explicit warning before the charge.

**I let a third-party embed inherit my design system.** Our global typography rules leaked into a vendor's embedded app and destroyed its layout — an 18px font floor and a couple of `!important` rules turned a product grid into a wall of text. Diagnosing it meant reading their stylesheet against their rendered markup and discovering their own build was mismatched. Lesson: an embedded surface needs an explicit isolation boundary, and you should assume the vendor's build can be broken too.

**I automated a publishing pipeline before I trusted it.** A scheduling API silently ignored the scheduled-time field and published a month of content in an hour. Nothing catastrophic, entirely avoidable: I had not verified that the vendor honored the parameter before handing it a queue. Now nothing is scheduled — things publish when a job fires, and the job reports what it did.

---

## What's in this repo

[`content-system/`](content-system/) — a real subsystem, extracted and self-contained.

Conceivable publishes a lot of visual content, and design consistency across it was a recurring failure. So the design system is code: templates render to images through a headless browser, which means brand rules (type scale, color roles, grain, layout rhythm) are enforced by the renderer rather than by whoever is making an asset that day.

It's a small piece of the product, but it's representative of how I work: notice the thing being done by hand repeatedly, encode the rules, remove the judgment call.

---

## Elsewhere

- [kirstenkarchmer.com](https://kirstenkarchmer.com)
- [conceivable.com](https://conceivable.com)
