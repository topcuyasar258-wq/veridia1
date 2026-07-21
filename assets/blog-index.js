!function(root){
  const pills=Array.from(document.querySelectorAll(".topic-pill[data-category]"));
  const cards=Array.from(document.querySelectorAll(".blog-card[data-category]"));
  const timers=new WeakMap();
  const defaultDisplay=new WeakMap();

  function show(card){
    if(card.dataset.visibility==="visible")return;
    root.clearTimeout(timers.get(card));
    card.style.display=defaultDisplay.get(card)||"flex";
    card.dataset.visibility="visible";
    root.requestAnimationFrame(()=>card.classList.remove("is-filtered-out"));
  }

  function hide(card){
    if(card.dataset.visibility==="hidden")return;
    root.clearTimeout(timers.get(card));
    card.dataset.visibility="hiding";
    card.classList.add("is-filtered-out");
    const timer=root.setTimeout(()=>{
      card.style.display="none";
      card.dataset.visibility="hidden";
    },320);
    timers.set(card,timer);
  }

  function filter(category){
    pills.forEach(pill=>pill.classList.toggle("is-active",pill.dataset.category===category));
    cards.forEach(card=>{
      if(category==="all"||card.dataset.category===category)show(card);
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
