module.exports = function(eleventyConfig) {
  // Copiar assets estáticos (CSS, JS, Imagens, Favicons)
  // Estes ficheiros serão copiados para a raiz da pasta de saída (_site)
  eleventyConfig.addPassthroughCopy("css");
  eleventyConfig.addPassthroughCopy("js");
  eleventyConfig.addPassthroughCopy("imagens");
  eleventyConfig.addPassthroughCopy("favicons");

  // Configurar as pastas de entrada e saída
  return {
    dir: {
      input: "./html", // Onde estão suas pastas de idioma (pt/, en/) e seus ficheiros de página
      includes: "../_includes", // Onde estão seus layouts e partials (base.html, header.html, footer.html)
      output: "_site" // A pasta de saída onde o Eleventy vai gerar o site final
    },
    // Definir o motor de template padrão para ficheiros HTML e Markdown
    // Nunjucks (njk) é o padrão e é uma boa escolha para HTML
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    dataTemplateEngine: "njk"
    pathPrefix: "/Bia/"
  };
};
