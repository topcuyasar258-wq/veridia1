!function(root){
  const pills=Array.from(document.querySelectorAll(".topic-pill[data-category]"));
  const cards=Array.from(document.querySelectorAll(".blog-card[data-category]"));
  const timers=new WeakMap();
  const defaultDisplay=new WeakMap();

  function show(card){
    root.clearTimeout(timers.get(card));
    const wasHidden=card.style.display==="none";
    card.style.display=defaultDisplay.get(card)||"flex";
    // display:none -> flex gecisinden sonra reflow zorlanmazsa tarayici iki
    // degisikligi tek karede birlestirir ve opacity gecisi calismaz.
    if(wasHidden)void card.offsetWidth;
    // Sinif senkron kaldirilir: requestAnimationFrame'e birakildiginda araya
    // giren bir hide() cagrisi karti kalici olarak saydam biraktiriyordu.
    card.classList.remove("is-filtered-out");
    card.dataset.visibility="visible";
  }

  function hide(card){
    if(card.dataset.visibility==="hidden")return;
    root.clearTimeout(timers.get(card));
    card.dataset.visibility="hiding";
    card.classList.add("is-filtered-out");
    const timer=root.setTimeout(()=>{
      if(card.dataset.visibility!=="hiding")return;
      card.style.display="none";
      card.dataset.visibility="hidden";
    },320);
    timers.set(card,timer);
  }

  function filter(category){
    pills.forEach(pill=>pill.classList.toggle("is-active",pill.dataset.category===category));
    cards.forEach(card=>{
      const categories=(card.dataset.category||"").split(/\s+/);
      if(category==="all"||categories.includes(category))show(card);
      else hide(card);
    });
  }

  if(pills.length&&cards.length){
    cards.forEach(card=>{
      defaultDisplay.set(card,getComputedStyle(card).display==="none"?"flex":getComputedStyle(card).display);
      card.dataset.visibility="visible";
    });
    pills.forEach(pill=>pill.addEventListener("click",()=>filter(pill.dataset.category||"all")));
    filter("all");
  }
}("undefined"!=typeof window?window:globalThis);
