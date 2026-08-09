/* =========================================================
   BOOKING WIZARD  (prefix: bk-)
   ---------------------------------------------------------
   Dùng chung cho public_booking.html (5 bước, có step Your
   Details) và customer_booking.html (4 bước, có loyalty
   points). KHÔNG phân nhánh theo cờ cấu hình: hai điểm khác
   nhau đều được feature-detect từ DOM.

     - Guest info: chỉ chạy khi có #full_name trong trang.
     - Loyalty points: chỉ chạy khi có #summary-points.

   Cấu hình do template đặt vào window.BOOKING_CONFIG trước
   khi nạp file này (giá trị Jinja + chuỗi đã dịch).

   THANH HÀNH ĐỘNG DÍNH ĐÁY (mobile) không dùng scroll
   listener. Một IntersectionObserver trên chính .bk-nav của
   bước đang mở: nút thật ngoài màn hình thì thanh hiện, nút
   thật vào màn hình thì thanh ẩn. Hai trạng thái bù trừ nhau
   nên luôn có đúng một nút Continue nhìn thấy được, và không
   bao giờ có hai cái cùng lúc.
   ========================================================= */

(function () {
  'use strict';

  var CFG = window.BOOKING_CONFIG || {};
  var T   = CFG.i18n || {};
  var DASH = '—';

  document.addEventListener('DOMContentLoaded', function () {

    var wrap = document.querySelector('.bk-wrap');
    if (!wrap) return;

    var steps    = Array.prototype.slice.call(document.querySelectorAll('.bk-step'));
    var dotWraps = document.querySelectorAll('.bk-step-dot-wrap');
    /* Hai thanh tiến độ: bản desktop (#progress-fill) và bản mobile trong
       dòng "Step X of Y". Cùng một giá trị. */
    var fills    = document.querySelectorAll('.bk-progress-fill, .bk-step-mobile-fill');
    var mobileLb = document.getElementById('bk-mobile-step');
    var total    = steps.length;
    var cur      = 1;

    /* =====================================================
       WIZARD
       ===================================================== */

    function activeStep() { return steps[cur - 1]; }

    function updateWizard() {
      steps.forEach(function (s, i) {
        s.classList.toggle('bk-step--active', i + 1 === cur);
      });

      dotWraps.forEach(function (w) {
        var n  = parseInt(w.dataset.step, 10);
        var d  = document.getElementById('step-circle-' + n);
        var lb = w.querySelector('.bk-step-label');
        if (!d) return;
        d.className  = 'bk-step-dot';
        if (lb) lb.className = 'bk-step-label';
        if (n < cur) {
          d.classList.add('bk-step-dot--done');
          d.innerHTML = '<span class="material-symbols-outlined bk-step-dot-check">check</span>';
          if (lb) lb.classList.add('bk-step-label--done');
        } else if (n === cur) {
          d.classList.add('bk-step-dot--active');
          d.textContent = n;
          if (lb) lb.classList.add('bk-step-label--active');
        } else {
          d.textContent = n;
        }
      });

      var pct = (((cur - 1) / (total - 1)) * 100) + '%';
      fills.forEach(function (f) { f.style.width = pct; });

      /* Ở mobile các nhãn bước bị ẩn, chấm số không nói được đang ở đâu.
         Dòng này là bản thay thế duy nhất đọc được trên màn hẹp.
         Ghép từ hai từ rời thay vì một chuỗi có %1/%2: chuỗi dịch trong
         codebase này phải escape '%' (xem 'VAT (25.5%%)'). */
      if (mobileLb) {
        var w   = document.querySelector('.bk-step-dot-wrap[data-step="' + cur + '"]');
        var nm  = w ? (w.dataset.label || '') : '';
        var pos = (T.stepWord || 'Step') + ' ' + cur + ' ' +
                  (T.ofWord || 'of') + ' ' + total;
        mobileLb.textContent = nm ? pos + ' · ' + nm : pos;
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });
      observeStep(activeStep());
      syncBar();
    }

    function goNext() { if (cur < total) { cur++; updateWizard(); } }
    function goBack() { if (cur > 1) { cur--; updateWizard(); } }

    document.querySelectorAll('.bk-btn-next').forEach(function (b) {
      b.addEventListener('click', goNext);
    });
    document.querySelectorAll('.bk-btn-back').forEach(function (b) {
      b.addEventListener('click', goBack);
    });

    /* =====================================================
       STEP 1 - LỌC THEO NHÓM + CHỌN DỊCH VỤ
       ===================================================== */

    var chips = document.querySelectorAll('.bk-chip');
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.forEach(function (c) { c.classList.remove('bk-chip--active'); });
        chip.classList.add('bk-chip--active');
        var filter = chip.dataset.category;
        document.querySelectorAll('.service-item').forEach(function (item) {
          item.style.display =
            (filter === 'all' || item.dataset.category === filter) ? '' : 'none';
        });
      });
    });

    function bindPicker(labelSel, cardSel, selectedCls) {
      document.querySelectorAll(labelSel).forEach(function (label) {
        label.addEventListener('click', function () {
          document.querySelectorAll(cardSel).forEach(function (c) {
            c.classList.remove(selectedCls);
          });
          var card = label.querySelector(cardSel);
          if (card) card.classList.add(selectedCls);
        });
      });
    }

    bindPicker('.bk-svc-label',     '.bk-svc-card',     'bk-svc-card--selected');
    bindPicker('.bk-staff-label',   '.bk-staff-card',   'bk-staff-card--selected');
    bindPicker('.bk-payment-label', '.bk-payment-card', 'bk-payment-card--selected');

    /* Đồng bộ trạng thái đã chọn sẵn từ server (preselect_id, No Preference,
       Pay at Salon) vào lớp CSS. */
    [['.service-radio:checked', '.bk-svc-label', '.bk-svc-card', 'bk-svc-card--selected'],
     ['.bk-staff-label input:checked', '.bk-staff-label', '.bk-staff-card', 'bk-staff-card--selected'],
     ['input[name="payment_method"]:checked', '.bk-payment-label', '.bk-payment-card', 'bk-payment-card--selected']
    ].forEach(function (t) {
      document.querySelectorAll(t[0]).forEach(function (r) {
        var host = r.closest(t[1]);
        var card = host && host.querySelector(t[2]);
        if (card) card.classList.add(t[3]);
      });
    });

    /* =====================================================
       TÓM TẮT + ĐIỂM THƯỞNG
       ===================================================== */

    var VAT = 0.255;

    function checkedService() { return document.querySelector('.service-radio:checked'); }
    function checkedStaff()   { return document.querySelector('input[name="staff_id"]:checked'); }

    function setText(id, val) {
      var el = document.getElementById(id);
      if (el) el.textContent = val;
    }

    function updateSummary() {
      var svc = checkedService();
      var stf = checkedStaff();

      if (svc) {
        var p   = parseFloat(svc.dataset.price) || 0;
        var vat = p * VAT;
        setText('summary-service-name', svc.dataset.name || DASH);
        setText('summary-duration',
          svc.dataset.duration ? svc.dataset.duration + ' ' + (T.min || 'min') : DASH);
        setText('summary-subtotal', '€' + p.toFixed(2));
        setText('summary-vat',      '€' + vat.toFixed(2));
        setText('summary-total',    '€' + (p + vat).toFixed(2));

        /* Chỉ customer flow có ô này. Guest flow không có -> bỏ qua. */
        if (document.getElementById('summary-points')) {
          var pts = Math.round((parseFloat(svc.dataset.points) || 0) *
                               (CFG.pointsMultiplier || 1));
          setText('summary-points', pts > 0 ? pts + ' ' + (T.pts || 'pts') : DASH);
        }
      }

      if (stf) setText('summary-staff', stf.dataset.name || T.noPreference || 'No Preference');
      syncBar();
    }

    document.querySelectorAll('.service-radio, input[name="staff_id"]').forEach(function (r) {
      r.addEventListener('change', updateSummary);
    });

    /* =====================================================
       STEP 4 GUEST - CHẶN CONTINUE KHI THIẾU THÔNG TIN
       Chỉ tồn tại ở public flow. Customer đã có sẵn hồ sơ.
       ===================================================== */

    var guestFields = ['full_name', 'phone', 'email']
                        .map(function (id) { return document.getElementById(id); });
    var hasGuestStep = guestFields.every(function (f) { return !!f; });
    var infoStepIdx  = hasGuestStep ? steps.indexOf(document.getElementById('step-4')) : -1;
    var infoNextBtn  = infoStepIdx > -1 ? steps[infoStepIdx].querySelector('.bk-btn-next') : null;

    function guestInfoValid() {
      if (!hasGuestStep) return true;
      var name  = guestFields[0].value.trim();
      var phone = guestFields[1].value.trim();
      var email = guestFields[2].value.trim();
      return name !== '' && phone !== '' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function syncInfoState() {
      if (infoNextBtn) infoNextBtn.disabled = !guestInfoValid();
      syncBar();
    }

    if (hasGuestStep) {
      guestFields.forEach(function (f) { f.addEventListener('input', syncInfoState); });
    }

    /* =====================================================
       LỊCH
       ===================================================== */

    var calendarEl   = document.getElementById('calendar');
    var timeGridEl   = document.getElementById('timeSlotGrid');
    var monthLabelEl = document.getElementById('calendarMonthLabel');
    var hiddenDate   = document.getElementById('hidden-booking-date');
    var hiddenTime   = document.getElementById('hidden-start-time');
    var dtStep       = document.getElementById('step-3');
    var dtNextBtn    = dtStep ? dtStep.querySelector('.bk-btn-next') : null;

    function parseLocalDate(s) {
      var p = s.split('-').map(Number);
      return new Date(p[0], p[1] - 1, p[2]);
    }

    function fmtDate(d) {
      return d.getFullYear() + '-' +
             String(d.getMonth() + 1).padStart(2, '0') + '-' +
             String(d.getDate()).padStart(2, '0');
    }

    var todayDate    = parseLocalDate(CFG.today);
    var maxDate      = parseLocalDate(CFG.maxDate);
    var selectedDate = todayDate;
    var currentMonth = new Date(todayDate.getFullYear(), todayDate.getMonth(), 1);

    function syncContinueState() {
      if (dtNextBtn) dtNextBtn.disabled = !hiddenTime.value;
      syncBar();
    }

    function calGridDates(monthDate) {
      var y = monthDate.getFullYear(), m = monthDate.getMonth();
      var offset = (new Date(y, m, 1).getDay() + 6) % 7;
      return Array.from({ length: 35 }, function (_, i) {
        return new Date(y, m, 1 - offset + i);
      });
    }

    function renderCalendar() {
      if (!calendarEl) return;
      monthLabelEl.textContent =
        currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      calendarEl.innerHTML = '';

      calGridDates(currentMonth).forEach(function (dateObj) {
        var isOther  = dateObj.getMonth() !== currentMonth.getMonth();
        var isPast   = dateObj < todayDate;
        var isFuture = dateObj > maxDate;
        var isToday  = fmtDate(dateObj) === CFG.today;
        var disabled = isOther || isPast || isFuture;

        var cell = document.createElement('div');
        cell.className = 'bk-cal-day';
        if (disabled) cell.classList.add('bk-cal-day--past');
        if (isToday)  cell.classList.add('bk-cal-day--today');
        if (selectedDate && fmtDate(dateObj) === fmtDate(selectedDate)) {
          cell.classList.add('bk-cal-day--selected');
        }
        cell.textContent = dateObj.getDate();

        if (!disabled) {
          cell.addEventListener('click', function () {
            selectedDate     = dateObj;
            hiddenDate.value = fmtDate(dateObj);
            hiddenTime.value = '';
            syncContinueState();
            renderCalendar();
            updateDatetimeSummary();
            tryLoadSlots();
          });
        }
        calendarEl.appendChild(cell);
      });
    }

    function updateDatetimeSummary() {
      var el = document.getElementById('summary-datetime');
      if (!el) return;
      var datePart = selectedDate
        ? selectedDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
        : DASH;
      el.textContent = hiddenTime.value ? datePart + ' · ' + hiddenTime.value : datePart;
      syncBar();
    }

    /* =====================================================
       KHUNG GIỜ
       ===================================================== */

    function placeholder(msg, icon) {
      timeGridEl.innerHTML = '';
      var box = document.createElement('div');
      box.className = 'bk-time-empty';
      if (icon) {
        var ic = document.createElement('span');
        ic.className = 'material-symbols-outlined bk-time-empty-icon';
        ic.textContent = icon;
        box.appendChild(ic);
      }
      var p = document.createElement('p');
      p.className = 'bk-time-empty-text';
      p.textContent = msg;
      box.appendChild(p);
      timeGridEl.appendChild(box);
    }

    /* Skeleton mang đúng hình dạng kết quả (một nhãn buổi + lưới pill),
       nên khi dữ liệu về không có cú nhảy bố cục. */
    function renderSkeleton() {
      timeGridEl.innerHTML = '';
      var group = document.createElement('div');
      group.className = 'bk-slot-group';
      var lb = document.createElement('div');
      lb.className = 'bk-slot-skeleton-label';
      group.appendChild(lb);
      var grid = document.createElement('div');
      grid.className = 'bk-slot-grid';
      for (var i = 0; i < 8; i++) {
        var s = document.createElement('div');
        s.className = 'bk-slot-skeleton';
        grid.appendChild(s);
      }
      group.appendChild(grid);
      timeGridEl.appendChild(group);
    }

    /* Chia theo buổi từ slot.value ("HH:MM"). Backend không đổi. */
    function bucketOf(value) {
      var h = parseInt(value.split(':')[0], 10);
      if (h < 12) return 'morning';
      if (h < 17) return 'afternoon';
      return 'evening';
    }

    function tryLoadSlots() {
      if (!timeGridEl) return;
      var svcEl = checkedService();
      if (!svcEl) {
        placeholder(T.selectService || 'Please select a service first.', 'spa');
        return;
      }
      if (!selectedDate) {
        placeholder(T.selectDate || 'Please select a date first.', 'event');
        return;
      }
      loadSlots(fmtDate(selectedDate), svcEl.value,
                (checkedStaff() && checkedStaff().value) || 0);
    }

    async function loadSlots(dateStr, svcId, stfId) {
      renderSkeleton();
      try {
        var res = await fetch(CFG.availableSlotUrl +
          '?booking_date=' + dateStr + '&staff_id=' + stfId + '&service_id=' + svcId);
        var data = await res.json();
        if (!res.ok) throw new Error(data.message || 'Failed');
        renderSlots(data.available_slots || []);
      } catch (e) {
        placeholder(T.loadError || 'Could not load available times.', 'error');
      }
    }

    function renderSlots(slots) {
      timeGridEl.innerHTML = '';
      hiddenTime.value = '';
      updateDatetimeSummary();
      syncContinueState();

      if (!slots.length) {
        placeholder(T.noSlots || 'No available slots for this date.', 'event_busy');
        return;
      }

      var buckets = { morning: [], afternoon: [], evening: [] };
      slots.forEach(function (s) { buckets[bucketOf(s.value)].push(s); });

      [['morning',   T.morning   || 'Morning'],
       ['afternoon', T.afternoon || 'Afternoon'],
       ['evening',   T.evening   || 'Evening']
      ].forEach(function (b) {
        var list = buckets[b[0]];
        if (!list.length) return;

        var group = document.createElement('div');
        group.className = 'bk-slot-group';

        var label = document.createElement('h4');
        label.className = 'bk-slot-group-label';
        label.textContent = b[1];
        group.appendChild(label);

        var grid = document.createElement('div');
        grid.className = 'bk-slot-grid';

        list.forEach(function (slot) {
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'slot-pill';
          btn.textContent = slot.label;
          if (slot.disabled) {
            btn.disabled = true;
          } else {
            btn.addEventListener('click', function () {
              timeGridEl.querySelectorAll('.slot-pill').forEach(function (p) {
                p.classList.remove('selected');
              });
              btn.classList.add('selected');
              hiddenTime.value = slot.value;
              updateDatetimeSummary();
              syncContinueState();
            });
          }
          grid.appendChild(btn);
        });

        group.appendChild(grid);
        timeGridEl.appendChild(group);
      });
    }

    /* =====================================================
       THANH HÀNH ĐỘNG DÍNH ĐÁY (mobile)
       ===================================================== */

    var bar        = document.getElementById('bk-sticky');
    var barNext    = document.getElementById('bk-sticky-next');
    var barBack    = document.getElementById('bk-sticky-back');
    var barCaption = document.getElementById('bk-sticky-caption');
    var barValue   = document.getElementById('bk-sticky-value');

    var navOnScreen = false;
    var navObs      = null;

    /* Thanh không tự xử lý gì: nó bấm hộ nút thật của bước đang đứng, nên
       mọi logic chặn/submit chỉ tồn tại một chỗ. */
    if (barNext) {
      barNext.addEventListener('click', function () {
        var stepEl  = activeStep();
        var confirm = stepEl && stepEl.querySelector('.bk-btn-confirm');
        if (confirm) confirm.click(); else goNext();
      });
    }
    if (barBack) barBack.addEventListener('click', goBack);

    /* Điều kiện duy nhất: nút thật của bước này có đang ở ngoài màn hình
       không. Không gắn thêm mốc "đã cuộn qua X" nữa - mốc đó đặt ở đâu cũng
       hỏng trên bước ngắn: bước 2 chỉ có 4 ô, cả trang cao ~680px nên tầm
       cuộn tối đa chỉ ~40-110px, không bao giờ vượt nổi một mốc nằm dưới
       tiêu đề. Hai trạng thái này bù trừ nhau nên khách luôn có đúng một nút
       Continue nhìn thấy được, ở mọi chiều cao nội dung. */
    function observeStep(stepEl) {
      if (navObs) { navObs.disconnect(); navObs = null; }
      navOnScreen = false;
      if (!stepEl || !bar) return;

      var nav = stepEl.querySelector('.bk-nav');
      if (!nav) return;

      navObs = new IntersectionObserver(function (entries) {
        navOnScreen = entries[0].isIntersecting;
        syncBar();
      }, { threshold: 0.15 });
      navObs.observe(nav);
    }

    /* Nội dung thanh nói đúng thứ vừa chọn ở bước đang đứng, nên nó vừa là
       nút bấm vừa là xác nhận. */
    function barContext() {
      var svc = checkedService();
      var stf = checkedStaff();

      if (cur === 1) {
        if (!svc) return null;
        var price = parseFloat(svc.dataset.price) || 0;
        return { caption: T.capService || 'Service',
                 value: (svc.dataset.name || '') + ' · €' + price.toFixed(2) };
      }
      if (cur === 2) {
        return { caption: T.capStylist || 'Stylist',
                 value: (stf && stf.dataset.name) || T.noPreference || 'No Preference' };
      }
      if (cur === 3) {
        var el = document.getElementById('summary-datetime');
        var v  = el ? el.textContent : '';
        return { caption: T.capWhen || 'Date & time',
                 value: (v && v !== DASH) ? v : (T.pickSlot || 'Pick a time slot') };
      }
      if (svc) {
        var p = parseFloat(svc.dataset.price) || 0;
        return { caption: T.capTotal || 'Total',
                 value: '€' + (p * (1 + VAT)).toFixed(2) };
      }
      return null;
    }

    function syncBar() {
      if (!bar) return;

      var stepEl   = activeStep();
      var realNext = stepEl ? stepEl.querySelector('.bk-btn-next, .bk-btn-confirm') : null;
      var visible  = !navOnScreen && !!realNext;

      bar.classList.toggle('bk-sticky--visible', visible);
      if (!visible) return;

      if (barBack) barBack.hidden = (cur === 1);

      if (barNext && realNext) {
        barNext.disabled = realNext.disabled;
        barNext.textContent = realNext.classList.contains('bk-btn-confirm')
          ? (T.confirmLabel  || 'Confirm')
          : (T.continueLabel || 'Continue');
      }

      var ctx = barContext();
      if (barCaption) barCaption.textContent = ctx ? ctx.caption : '';
      if (barValue)   barValue.textContent   = ctx ? ctx.value   : '';
    }

    /* =====================================================
       SUBMIT
       ===================================================== */

    var confirmBtn = document.getElementById('confirm-btn');
    var form = confirmBtn && confirmBtn.closest('form');
    if (form) {
      form.addEventListener('submit', function (e) {
        if (!guestInfoValid() || !hiddenTime.value) { e.preventDefault(); return; }
        confirmBtn.disabled = true;
        confirmBtn.textContent = T.processing || 'Processing...';
        if (barNext) barNext.disabled = true;
      });
    }

    /* =====================================================
       KHỞI TẠO
       ===================================================== */

    updateSummary();
    syncInfoState();
    syncContinueState();
    renderCalendar();
    if (hiddenDate) hiddenDate.value = fmtDate(selectedDate);
    updateDatetimeSummary();
    tryLoadSlots();

    document.querySelectorAll('.service-radio, input[name="staff_id"]').forEach(function (r) {
      r.addEventListener('change', tryLoadSlots);
    });

    var prevM = document.getElementById('prevMonth');
    var nextM = document.getElementById('nextMonth');
    if (prevM) prevM.addEventListener('click', function () {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
      renderCalendar();
    });
    if (nextM) nextM.addEventListener('click', function () {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
      renderCalendar();
    });

    updateWizard();
  });
})();
