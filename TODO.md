- [ ] Refactor `remove-no-cap` logic to filter out images *before* download:  
Instead of downloading all scraped images and removing those without captions afterward, update the logic to skip images without captions during scraping. Ensure the scraper continues fetching additional images until the target count of captioned images is reached.
