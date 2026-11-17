/**
 * Content for pages that are not built yet. Each entry lists the backlog
 * items (see docs/01-project-management/project-plan.md) it will contain.
 */
export const PLACEHOLDERS = {
  plan: {
    eyebrow: 'Monthly Plan',
    title: 'What you pay every month',
    lead: 'Rent, insurance, loan EMIs and every other obligation. Their total is your minimum monthly earning target.',
    sprint: 2,
    features: [
      'Recurring expense lines in any currency, valid from/to',
      'Loan EMIs added automatically',
      'Minimum monthly target in your base currency',
    ],
  },
  wallets: {
    eyebrow: 'Wallets',
    title: 'Your wallets',
    lead: 'One wallet per account or purpose: home account, daily spending, savings, proof of funds.',
    sprint: 1,
    features: [
      'Wallets in any currency with opening balance',
      'Income and expense transactions with categories and life phases',
      'Exchange rate frozen on every transaction',
    ],
  },
  remittances: {
    eyebrow: 'Remittances',
    title: 'Money sent and received',
    lead: 'Record transfers between your home and abroad accounts with the rate you really got.',
    sprint: 2,
    features: [
      'Enter amount sent and amount received; the real rate is calculated',
      'Comparison with the market rate of that day',
      'Hidden transfer cost in your base currency',
    ],
  },
  target: {
    eyebrow: 'Target to Earn',
    title: 'This month’s target',
    lead: 'How much you must earn this month to cover your plan, and how much you have earned and spent.',
    sprint: 2,
    features: [
      'Earned vs. minimum target with shortfall or surplus',
      'Earned by source and plan vs. actual per line',
      'Part-payment affordability estimate',
    ],
  },
  loans: {
    eyebrow: 'Loan Planner',
    title: 'Your loans',
    lead: 'Track EMIs and part-payments, interest paid and interest saved.',
    sprint: 2,
    features: [
      'Loans in any currency with editable outstanding amount',
      'EMI and part-payment recording with interest/principal split',
      'Months to payoff and interest saved by part-payments',
    ],
  },
  reports: {
    eyebrow: 'Reports',
    title: 'Progress over time',
    lead: 'Month, year, life phase or your whole journey since you started planning.',
    sprint: 3,
    features: [
      'Total cost of going abroad and cost of the degree',
      'Spending per phase and top categories',
      'Net-worth and loan payoff timelines',
    ],
  },
  profile: {
    eyebrow: 'Profile',
    title: 'Profile & life phases',
    lead: 'Your currencies, study dates and the phases of your journey.',
    sprint: 1,
    features: [
      'Registration and login',
      'Home and base currency, destination country, study dates',
      'Life phases created automatically and editable',
    ],
  },
}
