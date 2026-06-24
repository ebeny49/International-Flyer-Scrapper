# Source Reference

## Saudi Arabia

- Primary source: `https://d4donline.com/en/saudi-arabia/jeddah/`
- Search target: `https://d4donline.com/en/saudi-arabia/jeddah/products/43/tea-coffee?search=Tim%20Hortons`
- Extract product cards from `a.product-card`.
- Important attributes/classes:
  - `data-product-id`
  - `data-image-tr`
  - `data-url`
  - `data-pic-desc`
  - `.sub_txt`
  - `.product-amount`
  - `.offer_tag`
- Follow product links to validate the `Go to flyer` URL when available.

## Mexico

- Primary source: `https://timhortonsmx.com/es/promocionestyc.html`
- Split promotion blocks on `Promocion:` after accent normalization.
- Keep blocks with `Productos participantes:` and active `Valido del ... al ...` date ranges.
- Use the source page URL for `product_url` and `flyer_url` because the page is the official terms source.

## South Korea

- Known context: Tim Hortons packaged coffee has retail availability in South Korea, but a direct current retailer flyer source has not been confirmed.
- Leave `offers` empty unless a retailer page exposes current offer rows with item, price, validity, and offer link.
- Candidate retailers to investigate when asked: Lotte Mart, Lotte On, Emart/SSG, Coupang, and Naver Shopping. Prefer official retailer pages over news articles or general search snippets.
