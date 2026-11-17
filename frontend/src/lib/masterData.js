import api from '../api/client'

/** Currencies and countries rarely change: fetch once per page load. */
let cache = null

export function loadMasterData() {
  if (!cache) {
    cache = Promise.all([api.get('/currencies'), api.get('/countries')])
      .then(([cur, cty]) => ({ currencies: cur.data, countries: cty.data }))
      .catch((err) => {
        cache = null
        throw err
      })
  }
  return cache
}
