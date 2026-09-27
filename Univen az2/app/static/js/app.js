document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll("img[data-fallback]").forEach(img=>{
    img.addEventListener("error",()=>{
      img.src="data:image/svg+xml;charset=UTF-8,"+encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="550"><rect width="100%" height="100%" fill="#182235"/><text x="50%" y="50%" fill="#94a3b8" text-anchor="middle" font-family="Arial" font-size="28">Local room image</text></svg>`
      );
    },{once:true});
  });

  document.querySelectorAll("[data-carousel]").forEach(carousel=>{
    const imgs=[...carousel.querySelectorAll("img")]; let i=0;
    const show=n=>{i=(n+imgs.length)%imgs.length;imgs.forEach((x,j)=>x.classList.toggle("active",j===i));};
    carousel.querySelector("[data-prev]").addEventListener("click",()=>show(i-1));
    carousel.querySelector("[data-next]").addEventListener("click",()=>show(i+1));
  });

  const modal=document.querySelector("#detailsModal"), content=document.querySelector("#modalContent");
  document.querySelectorAll(".details-btn").forEach(btn=>btn.addEventListener("click",()=>{
    const d=JSON.parse(btn.dataset.listing);
    content.innerHTML=`<div class="eyebrow">LISTING DETAILS</div><h2>${d.name}</h2>
      <p><strong>Distance:</strong> ${d.distance}</p><p><strong>Address:</strong> ${d.address}</p>
      <p><strong>Contact:</strong> ${d.contact}</p><p><strong>Price:</strong> R ${Number(d.price).toLocaleString()}/month</p>
      <h3>Amenities</h3><ul>${d.amenities.map(x=>`<li>${x}</li>`).join("")}</ul>`;
    modal.classList.add("open"); modal.setAttribute("aria-hidden","false");
  }));
  document.querySelector(".modal-close")?.addEventListener("click",()=>{modal.classList.remove("open");modal.setAttribute("aria-hidden","true")});
  modal?.addEventListener("click",e=>{if(e.target===modal)modal.classList.remove("open")});

  document.querySelector("#listingFilter")?.addEventListener("change",e=>{
    document.querySelectorAll("tbody tr[data-listing]").forEach(row=>row.style.display=!e.target.value||row.dataset.listing===e.target.value?"":"none");
  });
});