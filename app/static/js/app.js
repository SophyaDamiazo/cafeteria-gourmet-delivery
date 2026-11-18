// Interacoes do front-end da Cafeteria Gourmet (JavaScript puro, sem bibliotecas).
document.addEventListener("DOMContentLoaded", () => {
  // Menu no celular
  const toggle = document.querySelector("[data-toggle-menu]");
  if (toggle) toggle.addEventListener("click", () => document.getElementById("menu").classList.toggle("aberto"));

  // Fechar avisos
  document.querySelectorAll("[data-fechar]").forEach((b) =>
    b.addEventListener("click", () => b.closest(".alerta").remove())
  );

  // Confirmacao antes de acoes irreversiveis (cancelar pedido)
  document.querySelectorAll("form[data-confirmar]").forEach((f) =>
    f.addEventListener("submit", (e) => {
      if (!confirm(f.dataset.confirmar)) e.preventDefault();
    })
  );

  // Alterar quantidade no carrinho envia o formulario automaticamente
  document.querySelectorAll("[data-auto-enviar]").forEach((i) =>
    i.addEventListener("change", () => i.form.submit())
  );

  // Botao de "olhinho" para mostrar/ocultar a senha
  const svg = (corpo) =>
    `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${corpo}</svg>`;
  const OLHO = svg('<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>');
  const OLHO_FECHADO = svg('<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>');
  document.querySelectorAll('input[type="password"]').forEach((campo) => {
    const caixa = document.createElement("div");
    caixa.className = "campo-senha";
    campo.parentNode.insertBefore(caixa, campo);
    caixa.appendChild(campo);
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "ver-senha";
    botao.innerHTML = OLHO;
    botao.setAttribute("aria-label", "Mostrar senha");
    botao.title = "Mostrar senha";
    botao.addEventListener("click", (e) => {
      e.preventDefault();
      const mostrar = campo.type === "password";
      campo.type = mostrar ? "text" : "password";
      botao.innerHTML = mostrar ? OLHO_FECHADO : OLHO;
      botao.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
      botao.title = mostrar ? "Ocultar senha" : "Mostrar senha";
      campo.focus();
    });
    caixa.appendChild(botao);
  });

  // Cadastro: confere se as senhas sao iguais antes de enviar
  const formCadastro = document.querySelector("form[data-validar-senha]");
  if (formCadastro) {
    formCadastro.addEventListener("submit", (e) => {
      const s = formCadastro.senha.value, c = formCadastro.confirmar_senha.value;
      if (s !== c) {
        e.preventDefault();
        formCadastro.confirmar_senha.setCustomValidity("As senhas não conferem.");
        formCadastro.confirmar_senha.reportValidity();
      }
    });
    formCadastro.confirmar_senha.addEventListener("input", (e) => e.target.setCustomValidity(""));
  }

  // Mascaras
  const mascara = (sel, fn) => document.querySelectorAll(sel).forEach((i) =>
    i.addEventListener("input", () => { i.value = fn(i.value.replace(/\D/g, "")); })
  );
  mascara("[data-mascara-telefone]", (d) => {
    d = d.slice(0, 11);
    if (d.length <= 2) return d;
    if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
    if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
    return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
  });
  mascara("[data-mascara-cartao]", (d) => d.slice(0, 16).replace(/(\d{4})(?=\d)/g, "$1 "));
  mascara("[data-mascara-validade]", (d) => (d.length > 2 ? `${d.slice(0, 2)}/${d.slice(2, 4)}` : d));

  // Checkout: mostra apenas os campos da forma de pagamento escolhida
  const checkout = document.getElementById("form-checkout");
  if (checkout) {
    const atualizar = () => {
      const forma = checkout.querySelector("input[name=forma_pagamento]:checked")?.value;
      checkout.querySelectorAll(".pag-detalhe").forEach((d) => {
        const ativo = d.dataset.forma === forma;
        d.hidden = !ativo;
        d.querySelectorAll("input").forEach((i) => {
          i.disabled = !ativo;
          i.required = ativo && forma === "Cartao";
        });
      });
    };
    checkout.querySelectorAll("input[name=forma_pagamento]").forEach((r) => r.addEventListener("change", atualizar));
    atualizar();
  }

  // Evita clique duplo no botao de pagar
  document.querySelectorAll("button[data-carregando]").forEach((b) =>
    b.form.addEventListener("submit", () => {
      setTimeout(() => { b.disabled = true; b.textContent = b.dataset.carregando; }, 0);
    })
  );

  // Acompanhamento do pedido: consulta o status a cada 10s e recarrega se mudar
  const acomp = document.getElementById("acompanhamento");
  if (acomp && !["Entregue", "Cancelado"].includes(acomp.dataset.status)) {
    setInterval(async () => {
      try {
        const r = await fetch(acomp.dataset.url, { headers: { Accept: "application/json" } });
        if (!r.ok) return;
        const dados = await r.json();
        if (dados.status !== acomp.dataset.status) location.reload();
      } catch (_) { /* sem conexao: tenta de novo no proximo ciclo */ }
    }, 10000);
  }
});
