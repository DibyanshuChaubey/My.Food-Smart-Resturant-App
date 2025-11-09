/* ============== UI: Navbar dropdowns & mobile drawer ============== */
(function(){
  const toggleDropdown = (el, open) => {
    el.classList.toggle('open', open);
  };

  // Hover + click support
  document.querySelectorAll('[data-dropdown]').forEach(dd=>{
    const trigger = dd.querySelector('[data-dropdown-trigger]');
    let hoverTimer;

    dd.addEventListener('mouseenter', ()=> {
      clearTimeout(hoverTimer);
      toggleDropdown(dd, true);
    });
    dd.addEventListener('mouseleave', ()=> {
      hoverTimer = setTimeout(()=>toggleDropdown(dd,false), 120);
    });
    trigger?.addEventListener('click', (e)=>{
      e.stopPropagation();
      toggleDropdown(dd, !dd.classList.contains('open'));
    });
  });

  document.addEventListener('click', ()=> {
    document.querySelectorAll('.dropdown.open').forEach(d=>d.classList.remove('open'));
  });

  // Mobile drawer
  const mobileBtn = document.getElementById('mobileMenuBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  const orderNowMobile = document.getElementById('confirmOrderBtnMobile');
  if (mobileBtn && mobileMenu){
    mobileBtn.addEventListener('click', ()=> mobileMenu.classList.toggle('hidden'));
  }
  orderNowMobile?.addEventListener('click', ()=>{
    document.getElementById("menu")?.scrollIntoView({behavior:"smooth"});
    mobileMenu.classList.add('hidden');
  });
})();

/* ============== Cart & Order (keeps your original IDs/classes) ============== */
const orderItems = [];
const summaryEl = document.getElementById('order-summary');
const totalEl = document.getElementById('order-total');
const checkoutSection = document.getElementById('order'); // panel wraps form
const deliverySelect = document.getElementById('delivery-method');
const addressWrapper = document.getElementById('address-wrapper');
const confirmOrderBtn = document.getElementById('confirmOrderBtn');

/* Render summary */
function renderSummary(){
  if (!summaryEl || !totalEl) return;
  summaryEl.innerHTML = '';
  let total = 0;
  if (orderItems.length === 0){
    summaryEl.innerHTML = '<p class="text-ivory/60 italic">No items yet. Please add something from the menu.</p>';
  } else {
    orderItems.forEach(item=>{
      total += item.price * item.quantity;
      const row = document.createElement('div');
      row.className = 'flex justify-between items-center gap-3';
      row.innerHTML = `
        <span>${item.name}</span>
        <span>$${item.price.toFixed(2)} × ${item.quantity}</span>
        <button class="text-red-400 hover:text-red-300 text-sm" data-remove="${item.name}">Remove</button>
      `;
      summaryEl.appendChild(row);
    });
  }
  totalEl.textContent = `Total: $${total.toFixed(2)}`;

  // remove handlers
  summaryEl.querySelectorAll('[data-remove]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const name = btn.getAttribute('data-remove');
      const idx = orderItems.findIndex(i=>i.name===name);
      if (idx>-1) orderItems.splice(idx,1);
      // re-enable add button
      document.querySelectorAll('.dish-card').forEach(card=>{
        const title = card.querySelector('.card-title')?.textContent?.trim();
        if (title === name){
          const addBtn = card.querySelector('.add-to-order');
          if (addBtn){ addBtn.disabled=false; addBtn.textContent='Add'; }
          const qty = card.querySelector('.dish-qty'); if (qty) qty.value = 1;
        }
      });
      renderSummary();
    });
  });
}

/* Add-to-order */
document.querySelectorAll('.add-to-order').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    const card = btn.closest('.dish-card');
    const name = card.querySelector('.card-title').textContent.trim();
    const price = parseFloat(card.querySelector('.dish-price').textContent.replace('$',''));
    const qty = parseInt(card.querySelector('.dish-qty').value || '1', 10);
    if (!qty || qty<1) return alert('Please enter a valid quantity.');
    const existing = orderItems.find(i=>i.name===name);
    if (existing) existing.quantity += qty;
    else orderItems.push({ name, price, quantity: qty });
    btn.disabled = true; btn.textContent = '✔ Added';
    renderSummary();
    document.getElementById('order')?.scrollIntoView({behavior:'smooth'});
  });
});

/* Category filter */
document.querySelectorAll('.menu-category').forEach(chip=>{
  chip.addEventListener('click', ()=>{
    const cat = chip.getAttribute('data-cat');
    document.querySelectorAll('.dish-card').forEach(card=>{
      const c = card.getAttribute('data-category');
      card.classList.toggle('hidden', !(cat==='all' || c===cat));
    });
  });
});

/* Delivery toggle */
deliverySelect?.addEventListener('change', ()=>{
  if (deliverySelect.value === 'delivery') addressWrapper?.classList.remove('hidden');
  else { addressWrapper?.classList.add('hidden'); const addr=document.getElementById('address'); if (addr) addr.value=''; }
});

/* Order Now buttons smooth scroll */
confirmOrderBtn?.addEventListener('click', ()=>{
  document.getElementById("menu")?.scrollIntoView({behavior:"smooth"});
});

/* Clear cart */
document.getElementById('clearCart')?.addEventListener('click', ()=>{
  orderItems.length = 0;
  renderSummary();
  document.querySelectorAll('.add-to-order').forEach(b=>{ b.disabled=false; b.textContent='Add'; });
  document.querySelectorAll('.dish-qty').forEach(q=>q.value=1);
});

/* Submit order with login-preserve */
document.getElementById('reservationForm')?.addEventListener('submit', async (e)=>{
  e.preventDefault();
  if (orderItems.length===0) return alert('Please add items to your order.');

  const payload = {
    customer:{
      name: document.getElementById('name').value,
      email: document.getElementById('email').value,
      phone: document.getElementById('phone').value
    },
    delivery:{
      method: deliverySelect.value,
      address: document.getElementById('address')?.value || '',
      specialRequests: document.getElementById('specialRequests')?.value || ''
    },
    items: orderItems,
    total: orderItems.reduce((s,i)=>s+i.price*i.quantity,0)
  };

  try{
    const res = await fetch('/customer/api/orders',{
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.login_required){
      sessionStorage.setItem('pendingOrder', JSON.stringify(payload));
      sessionStorage.setItem('redirectAfterLogin','/#order');
      location.href = '/otp_login';
      return;
    }

    if (res.ok && data.success){
      alert(`✅ Order confirmed! ID: ${data.order_id}`);
      resetAll();
    } else {
      alert('⚠️ '+(data.error||'Something went wrong.'));
    }
  }catch(err){
    console.error(err);
    alert('⚠️ Network error. Please try again.');
  }
});

function resetAll(){
  orderItems.length = 0; renderSummary();
  document.getElementById('reservationForm').reset();
  addressWrapper?.classList.add('hidden');
  document.querySelectorAll('.add-to-order').forEach(b=>{ b.disabled=false; b.textContent='Add'; });
  document.querySelectorAll('.dish-qty').forEach(q=>q.value=1);
}

/* ============== Private Room ============== */
(function(){
  const showBtn = document.getElementById('showPrivateRoomForm');
  const wrap = document.getElementById('privateRoomFormWrapper');
  const form = document.getElementById('privateRoomForm');

  showBtn?.addEventListener('click', ()=>{
    wrap.classList.toggle('hidden');
    if (!wrap.classList.contains('hidden')) wrap.scrollIntoView({behavior:'smooth'});
  });

  form?.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const formData = {
      name: form.querySelector('input[placeholder="Your Name"]').value.trim(),
      email: form.querySelector('input[placeholder="Email"]').value.trim(),
      date: form.querySelector('input[type="date"]').value.trim(),
      time: form.querySelector('input[type="time"]').value.trim(),
      message: form.querySelector('textarea').value.trim(),
    };
    try{
      const res = await fetch('/customer/api/private-room',{
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(formData)
      });
      const result = await res.json();

      if (result.login_required){
        sessionStorage.setItem('pendingPrivateRoom', JSON.stringify(formData));
        sessionStorage.setItem('redirectAfterLogin','/#private-rooms');
        location.href='/otp_login'; return;
      }
      if (res.ok && result.success){
        alert('✅ Private room booked!');
        form.reset(); wrap.classList.add('hidden');
      } else alert('⚠️ '+(result.error||'Something went wrong.'));
    }catch(err){
      console.error(err); alert('⚠️ Network error.');
    }
  });
})();

/* ============== Event Reservation ============== */
(function(){
  const showBtn = document.getElementById('showEventForm');
  const wrap = document.getElementById('eventFormWrapper');
  const form = document.getElementById('eventReservationForm');

  showBtn?.addEventListener('click', ()=>{
    wrap.classList.toggle('hidden');
    if (!wrap.classList.contains('hidden')) wrap.scrollIntoView({behavior:'smooth'});
  });

  form?.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const formData = {
      name: form.querySelector('input[placeholder="Your Name"]').value.trim(),
      email: form.querySelector('input[placeholder="Email"]').value.trim(),
      event_type: form.querySelector('input[placeholder="Event Type (Wedding, Party, etc.)"]').value.trim(),
      guests: form.querySelector('input[placeholder="Number of Guests"]').value.trim(),
      date: form.querySelector('input[type="date"]').value.trim(),
      message: form.querySelector('textarea').value.trim()
    };
    try{
      const res = await fetch('/customer/api/event-reservation',{
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(formData)
      });
      const result = await res.json();

      if (result.login_required){
        sessionStorage.setItem('pendingEvent', JSON.stringify(formData));
        sessionStorage.setItem('redirectAfterLogin','/#event-reservation');
        location.href='/otp_login'; return;
      }
      if (res.ok && result.success){
        alert('✅ Event reserved!');
        form.reset(); wrap.classList.add('hidden');
      } else alert('⚠️ '+(result.error||'Something went wrong.'));
    }catch(err){
      console.error(err); alert('⚠️ Network error.');
    }
  });
})();

/* ============== Restore pending after login ============== */
window.addEventListener('load', ()=>{
  const redirect = sessionStorage.getItem('redirectAfterLogin');
  if (redirect){ sessionStorage.removeItem('redirectAfterLogin'); location.hash = redirect.split('#')[1] || ''; }
  renderSummary();
});
