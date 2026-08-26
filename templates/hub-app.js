const rows = /*__ROWS__*/;
    const stageCards = /*__STAGE_CARDS__*/;
    const primaryStageCards = /*__STAGE_CARDS__*/;
    const onboardingStageCards = /*__ONBOARDING_STAGE_CARDS__*/;
    const epOpsStageCards = /*__EP_OPS_STAGE_CARDS__*/;
    const epInstallationStageCards = /*__EP_INSTALLATION_STAGE_CARDS__*/;
    const secondaryStageCards = /*__SECONDARY_STAGE_CARDS__*/;
    const els = {
      onboardingStageGrid: document.getElementById('onboardingStageGrid'),
      epOpsStageGrid: document.getElementById('epOpsStageGrid'),
      epInstallationStageGrid: document.getElementById('epInstallationStageGrid'),
      secondaryStageGrid: document.getElementById('secondaryStageGrid'),
      searchFilter: document.getElementById('searchFilter'),
      assignedRepFilter: document.getElementById('assignedRepFilter'),
      assignedRepToggle: document.getElementById('assignedRepToggle'),
      assignedRepMenu: document.getElementById('assignedRepMenu'),
      stageFilter: document.getElementById('stageFilter'),
      createdYearFilter: document.getElementById('createdYearFilter'),
      resetFilters: document.getElementById('resetFilters'),
      overdueToggle: document.getElementById('overdueToggle'),
      stageDetail: document.getElementById('stageDetail'),
      activeJobsValue: document.getElementById('activeJobsValue'),
      activeJobsDetail: document.getElementById('activeJobsDetail'),
      heldJobsValue: document.getElementById('heldJobsValue'),
      heldJobsDetail: document.getElementById('heldJobsDetail'),
      overSlaValue: document.getElementById('overSlaValue'),
      overSlaDetail: document.getElementById('overSlaDetail'),
      installTimeValue: document.getElementById('installTimeValue'),
      installTimeDetail: document.getElementById('installTimeDetail'),
      tableBody: document.getElementById('tableBody'),
      tableMeta: document.getElementById('tableMeta'),
      tableWrap: document.querySelector('.table-wrap'),
      tableScrollbar: document.getElementById('tableScrollbar'),
      tableScrollbarTrack: document.getElementById('tableScrollbarTrack'),
      openCancellationModal: document.getElementById('openCancellationModal'),
      cancellationModal: document.getElementById('cancellationModal'),
      closeCancellationModal: document.getElementById('closeCancellationModal'),
      cancellationChart: document.getElementById('cancellationChart'),
      cancellationRepFilter: document.getElementById('cancellationRepFilter'),
      cancellationRepToggle: document.getElementById('cancellationRepToggle'),
      cancellationRepMenu: document.getElementById('cancellationRepMenu'),
      cancellationRepSearch: document.getElementById('cancellationRepSearch'),
      assignedRepSearch: document.getElementById('assignedRepSearch'),
      cancellationLatestMonth: document.getElementById('cancellationLatestMonth'),
      cancellationLatestDetail: document.getElementById('cancellationLatestDetail'),
      cancellationLatestRate: document.getElementById('cancellationLatestRate'),
      cancellationLatestRateDetail: document.getElementById('cancellationLatestRateDetail'),
      cancellationLatestCounts: document.getElementById('cancellationLatestCounts'),
      cancellationLatestCountsDetail: document.getElementById('cancellationLatestCountsDetail'),
      cancellationStageList: document.getElementById('cancellationStageList'),
    };
    const filterState = {
      overdueOnly: false,
    };

    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function slugify(value) {
      return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    }

    function selectedStage() {
      return els.stageFilter.value.trim();
    }


    function filterRepMenu(menuEl, query) {
      const needle = String(query || '').trim().toLowerCase();
      menuEl.querySelectorAll('.multi-select-option').forEach((option) => {
        const label = (option.textContent || '').trim().toLowerCase();
        option.hidden = Boolean(needle) && !label.includes(needle);
      });
    }

    function selectedAssignedReps() {
      return new Set(
        Array.from(els.assignedRepMenu.querySelectorAll('input:checked'))
          .map((input) => input.value.trim().toLowerCase())
      );
    }

    function updateAssignedRepLabel() {
      const checked = Array.from(els.assignedRepMenu.querySelectorAll('input:checked'));
      els.assignedRepToggle.textContent = checked.length === 0
        ? 'All Assigned Reps'
        : checked.length === 1
          ? checked[0].value
          : `${checked.length} reps selected`;
    }

    function selectedCancellationReps() {
      return new Set(
        Array.from(els.cancellationRepMenu.querySelectorAll('input:checked'))
          .map((input) => input.value.trim().toLowerCase())
      );
    }

    function updateCancellationRepLabel() {
      const checked = Array.from(els.cancellationRepMenu.querySelectorAll('input:checked'));
      els.cancellationRepToggle.textContent = checked.length === 0
        ? 'All Sales Reps'
        : checked.length === 1
          ? checked[0].value
          : `${checked.length} reps selected`;
    }

    function cancellationRows() {
      const selectedReps = selectedCancellationReps();
      if (!selectedReps.size) return rows;
      return rows.filter((row) => selectedReps.has(String(row.assigned_rep || '').trim().toLowerCase()));
    }

    function hasSla(row) {
      return row && row.sla_days !== '' && row.sla_days !== null && typeof row.sla_days !== 'undefined';
    }

    function createdYear(row) {
      const iso = String(row.created_at_iso || '').trim();
      return iso ? iso.slice(0, 4) : '';
    }

    function createdMonthKey(row) {
      const iso = String(row.created_at_iso || '').trim();
      return iso ? iso.slice(0, 7) : '';
    }

    function formatMonthLabel(monthKey) {
      if (!monthKey) return '—';
      const parts = monthKey.split('-');
      if (parts.length !== 2) return monthKey;
      const [year, month] = parts;
      const monthNumber = Number(month);
      const yearNumber = Number(year);
      if (!Number.isInteger(monthNumber) || monthNumber < 1 || monthNumber > 12) return monthKey;
      if (!Number.isInteger(yearNumber)) return monthKey;
      const mm = String(monthNumber).padStart(2, '0');
      const yy = String(yearNumber).slice(-2);
      return `${mm}/${yy}`;
    }

    function percentText(value) {
      return `${(Math.round(value * 10) / 10).toFixed(1)}%`;
    }

    function filteredRows(options = {}) {
      const ignoreStage = Boolean(options.ignoreStage);
      const search = els.searchFilter.value.trim().toLowerCase();
      const assignedReps = selectedAssignedReps();
      const stage = selectedStage().toLowerCase();
      const createdYearValue = els.createdYearFilter.value.trim();
      return rows.filter((row) => {
        if (filterState.overdueOnly && !row.is_over_sla) return false;
        if (!ignoreStage && stage && String(row.pm_bucket || '').trim().toLowerCase() !== stage) return false;
        if (assignedReps.size && !assignedReps.has(String(row.assigned_rep || '').trim().toLowerCase())) return false;
        if (createdYearValue && createdYear(row) !== createdYearValue) return false;
        if (search) {
          const haystack = [
            row.pm_bucket,
            row.process_bucket,
            row.display_name,
            row.assigned_rep,
            row.address,
            row.zip_code,
            row.permit_ahj,
            row.permit_phone,
            row.permit_tat,
            row.site_survey_date,
            row.first_installed_on,
            row.task_status,
            row.calc_status,
            row.finance_status,
            row.permit_status,
            row.interconnection_status,
            row.monitoring_approval,
            row.monitoring_status,
            row.process_board_note,
            row.essential_view_note,
          ].join(' ').toLowerCase();
          if (!haystack.includes(search)) return false;
        }
        return true;
      });
    }

    function rowsForSummary() {
      return filteredRows({ ignoreStage: true });
    }

    function sortedRows(list) {
      return [...list].sort((a, b) => {
        const stageCmp = String(a.pm_bucket || '').localeCompare(String(b.pm_bucket || ''), undefined, { sensitivity: 'base' });
        if (stageCmp) return stageCmp;
        const dayCmp = Number(b.days_in_bucket || 0) - Number(a.days_in_bucket || 0);
        if (dayCmp) return dayCmp;
        return String(a.display_name || '').localeCompare(String(b.display_name || ''), undefined, { sensitivity: 'base', numeric: true });
      });
    }

    function syncTableScrollbar() {
      if (!els.tableWrap || !els.tableScrollbar || !els.tableScrollbarTrack) return;
      const width = Math.max(els.tableWrap.scrollWidth, els.tableWrap.clientWidth);
      els.tableScrollbarTrack.style.width = `${width}px`;
      els.tableScrollbar.scrollLeft = els.tableWrap.scrollLeft;
    }

    function summarizeRows(list) {
      const activeJobs = list.filter((row) => ['onboarding', 'ep_ops'].includes(String(row.section || ''))).length;
      const heldJobs = list.filter((row) => String(row.section || '') === 'hold_cancel').length;
      const overdueJobs = list.filter((row) => row.is_over_sla).length;
      const installValues = list
        .map((row) => {
          const value = String(row.install_cycle_days ?? '').trim();
          return value === '' ? null : Number(value);
        })
        .filter((value) => Number.isFinite(value));
      let medianInstall = null;
      if (installValues.length) {
        const sorted = [...installValues].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);
        medianInstall = sorted.length % 2
          ? sorted[middle]
          : Math.round(((sorted[middle - 1] + sorted[middle]) / 2) * 10) / 10;
      }
      return {
        activeJobs,
        heldJobs,
        overdueJobs,
        medianInstall,
        installSampleSize: installValues.length,
      };
    }

    function cancellationSeries() {
      const monthly = new Map();
      cancellationRows().forEach((row) => {
        const monthKey = createdMonthKey(row);
        if (!monthKey) return;
        if (monthKey < '2026-01') return;
        if (!monthly.has(monthKey)) {
          monthly.set(monthKey, { monthKey, created: 0, cancelled: 0 });
        }
        const bucket = String(row.pm_bucket || '').trim().toLowerCase();
        const item = monthly.get(monthKey);
        item.created += 1;
        if (bucket === 'cancelled') {
          item.cancelled += 1;
        }
      });
      const currentMonth = new Date().toISOString().slice(0, 7);
      const completeSeries = [];
      let cursor = new Date('2026-01-01T00:00:00Z');
      const end = new Date(`${currentMonth}-01T00:00:00Z`);
      while (cursor <= end) {
        const monthKey = cursor.toISOString().slice(0, 7);
        completeSeries.push(monthly.get(monthKey) || { monthKey, created: 0, cancelled: 0 });
        cursor.setUTCMonth(cursor.getUTCMonth() + 1);
      }
      return completeSeries
        .map((item) => ({
          ...item,
          rate: item.created ? (item.cancelled / item.created) * 100 : 0,
          label: formatMonthLabel(item.monthKey),
        }));
    }

    function renderCancellationChart() {
      if (!els.cancellationChart) return;
      const series = cancellationSeries();
      if (!series.length) {
        els.cancellationChart.innerHTML = '<text x="50%" y="50%" text-anchor="middle" class="chart-axis">No cancellation data available.</text>';
        els.cancellationLatestMonth.textContent = '—';
        els.cancellationLatestRate.textContent = '—';
        els.cancellationLatestCounts.textContent = '—';
        return;
      }

      const width = 900;
      const height = 360;
      const margin = { top: 24, right: 28, bottom: 56, left: 56 };
      const chartWidth = width - margin.left - margin.right;
      const chartHeight = height - margin.top - margin.bottom;
      const maxRate = Math.max(10, ...series.map((point) => point.rate), 100);
      const gridValues = [0, 25, 50, 75, 100];
      const xStep = series.length > 1 ? chartWidth / (series.length - 1) : 0;
      const xFor = (index) => margin.left + (series.length > 1 ? index * xStep : chartWidth / 2);
      const yFor = (value) => margin.top + chartHeight - (Math.min(value, maxRate) / maxRate) * chartHeight;
      const path = series.map((point, index) => `${index === 0 ? 'M' : 'L'} ${xFor(index).toFixed(2)} ${yFor(point.rate).toFixed(2)}`).join(' ');

      const grid = gridValues.map((value) => {
        const y = yFor(value);
        return `
          <line class="chart-grid" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}"></line>
          <text class="chart-axis" x="${margin.left - 10}" y="${y + 4}" text-anchor="end">${value}%</text>
        `;
      }).join('');

      const points = series.map((point, index) => {
        const x = xFor(index);
        const y = yFor(point.rate);
        const detailUrl = `happy-slr-hold-cancelled.html?createdMonth=${encodeURIComponent(point.monthKey)}&bucket=Cancelled&totalJobs=${point.created}&totalCancels=${point.cancelled}`;
        return `
          <a href="${detailUrl}" aria-label="View cancellations created in ${escapeHtml(point.label)}">
            <circle class="chart-point" cx="${x}" cy="${y}" r="9"></circle>
          </a>
          <text class="chart-point-label" x="${x}" y="${y - 14}" text-anchor="middle">${percentText(point.rate)}</text>
          <a href="${detailUrl}" aria-label="View cancellations created in ${escapeHtml(point.label)}">
            <text class="chart-axis" x="${x}" y="${height - 18}" text-anchor="middle" style="cursor:pointer;text-decoration:underline">${escapeHtml(point.label)}</text>
          </a>
        `;
      }).join('');

      els.cancellationChart.innerHTML = `
        <rect x="0" y="0" width="${width}" height="${height}" rx="20" fill="transparent"></rect>
        ${grid}
        <line class="chart-grid" x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}"></line>
        <path class="chart-line" d="${path}"></path>
        ${points}
      `;

      const latest = [...series].reverse().find((item) => item.created > 0) || series[series.length - 1];
      els.cancellationLatestMonth.textContent = latest.label;
      els.cancellationLatestDetail.textContent = `Latest month in the created-date series: ${latest.monthKey}.`;
      els.cancellationLatestRate.textContent = percentText(latest.rate);
      els.cancellationLatestRateDetail.textContent = `Cancellation percentage for ${latest.label} based on created month.`;
      els.cancellationLatestCounts.textContent = `${latest.cancelled} / ${latest.created}`;
      els.cancellationLatestCountsDetail.textContent = `Cancelled sales over total sales created in ${latest.label}.`;
      renderCancellationStages();
    }

    function renderCancellationStages() {
      if (!els.cancellationStageList) return;
      const counts = new Map();
      cancellationRows().forEach((row) => {
        if (String(row.pm_bucket || '').trim().toLowerCase() !== 'cancelled') return;
        const stage = String(row.cancel_source_stage || '').trim() || 'Unknown prior stage';
        counts.set(stage, (counts.get(stage) || 0) + 1);
      });
      const total = Array.from(counts.values()).reduce((sum, count) => sum + count, 0);
      if (!total) {
        els.cancellationStageList.innerHTML = '<div class="empty-state">No cancellation transition history available.</div>';
        return;
      }
      const sorted = Array.from(counts, ([stage, count]) => ({ stage, count }))
        .sort((a, b) => b.count - a.count || a.stage.localeCompare(b.stage));
      const leading = sorted.slice(0, 10);
      const otherCount = sorted.slice(10).reduce((sum, item) => sum + item.count, 0);
      if (otherCount) leading.push({ stage: 'Other historical stages', count: otherCount });
      els.cancellationStageList.innerHTML = leading.map((item) => {
        const percentage = (item.count / total) * 100;
        return `
          <div class="cancel-stage-row">
            <div class="cancel-stage-name">${escapeHtml(item.stage)}</div>
            <div class="cancel-stage-track"><div class="cancel-stage-fill" style="width:${percentage.toFixed(1)}%"></div></div>
            <div class="cancel-stage-value">${percentage.toFixed(1)}% · ${item.count}</div>
          </div>
        `;
      }).join('');
    }

    function openCancellationModal() {
      renderCancellationChart();
      els.cancellationModal.hidden = false;
      document.body.style.overflow = 'hidden';
    }

    function closeCancellationModal() {
      els.cancellationModal.hidden = true;
      document.body.style.overflow = '';
    }

    function renderOverview() {
      const baseRows = rowsForSummary();
      const summary = summarizeRows(baseRows);
      els.activeJobsValue.textContent = String(summary.activeJobs);
      els.activeJobsDetail.textContent = `Happy Slr jobs in Onboarding and EP Ops only. Hold/cancel and EP Installation are excluded. Based on ${baseRows.length} filtered project(s).`;
      els.heldJobsValue.textContent = String(summary.heldJobs);
      els.heldJobsDetail.textContent = `Jobs currently sitting in hold, cancelled, or finalized/archive-style buckets. Based on ${baseRows.length} filtered project(s).`;
      els.overSlaValue.textContent = String(summary.overdueJobs);
      els.overSlaDetail.textContent = 'Projects whose days in bucket currently exceed the SLA mapped from the EP stage sheet.';
      els.installTimeValue.textContent = summary.medianInstall === null ? '—' : String(summary.medianInstall);
      els.installTimeDetail.textContent = `Median days from project creation to the earliest Essential View install date across ${summary.installSampleSize} filtered Happy Slr project(s) with an install date.`;
    }

    function renderStageFilterOptions(cards) {
      const priorValue = els.stageFilter.value;
      els.stageFilter.innerHTML = ['<option value="">All Buckets</option>'].concat(
        cards.map((card) => `<option value="${escapeHtml(card.stage)}">${escapeHtml(card.stage)} (${escapeHtml(card.count)})</option>`)
      ).join('');
      if (cards.some((card) => card.stage === priorValue)) {
        els.stageFilter.value = priorValue;
        return;
      }
      const fromHash = cards.find((card) => `#${card.stage_slug}` === window.location.hash);
      if (fromHash) {
        els.stageFilter.value = fromHash.stage;
      }
    }

    function renderCreatedYearFilterOptions() {
      const years = Array.from(new Set(rows.map((row) => createdYear(row)).filter(Boolean))).sort().reverse();
      const preferredDefault = '';
      els.createdYearFilter.innerHTML = [
        '<option value="">All Years</option>',
        ...years.map((year) => `<option value="${escapeHtml(year)}">Created in ${escapeHtml(year)}</option>`),
      ].join('');
      els.createdYearFilter.value = preferredDefault;
    }

    function cardsForDisplay(cards) {
      const baseRows = rowsForSummary();
      const countByBucket = new Map();
      const overdueByBucket = new Map();
      baseRows.forEach((row) => {
        const bucket = String(row.pm_bucket || '');
        countByBucket.set(bucket, (countByBucket.get(bucket) || 0) + 1);
        if (row.is_over_sla) {
          overdueByBucket.set(bucket, (overdueByBucket.get(bucket) || 0) + 1);
        }
      });
      return cards.map((card) => ({
        ...card,
        count: countByBucket.get(card.stage) || 0,
        overdue_count: overdueByBucket.get(card.stage) || 0,
      }));
    }

    function renderStageCards(gridEl, cards) {
      const displayCards = cardsForDisplay(cards);
      const selected = selectedStage();
      gridEl.innerHTML = displayCards.map((card) => {
        const active = selected === card.stage ? ' active' : '';
        const overdueActive = filterState.overdueOnly && selected === card.stage ? ' overdue-active' : '';
        const fullName = card.full_name || card.stage || '';
        const displayLabel = card.display_label || card.short_label || card.stage || '';
        const slaText = card.sla_mode === 'zip'
          ? 'SLA: ZIP-based'
          : card.sla_days
            ? `SLA: ${card.sla_days} day${card.sla_days === 1 ? '' : 's'}`
            : 'SLA: not set';
        const overdueText = card.overdue_count ? `${card.overdue_count} overdue` : '0 overdue';
        const overdueClass = card.overdue_count ? ' has-overdue' : '';
        const overdueButtonClass = filterState.overdueOnly && selected === card.stage ? ' active' : '';
        return `
          <article class="card stage-card${active}${overdueActive}" data-stage="${escapeHtml(card.stage)}" title="${escapeHtml(fullName)}" aria-label="${escapeHtml(fullName)}">
            <div class="stage-top">
              <div class="stage-name" title="${escapeHtml(fullName)}">${escapeHtml(displayLabel)}</div>
              <div class="stage-count">${escapeHtml(card.count)}</div>
              <div class="stage-meta">
                <div class="stage-sla">${escapeHtml(slaText)}</div>
                <button class="stage-overdue-button${overdueClass}${overdueButtonClass}" type="button" data-overdue-stage="${escapeHtml(card.stage)}">${escapeHtml(overdueText)}</button>
              </div>
            </div>
          </article>
        `;
      }).join('');
      gridEl.querySelectorAll('.stage-card').forEach((cardEl) => {
        cardEl.addEventListener('click', (event) => {
          if (event.target.closest('.stage-overdue-button')) return;
          const stage = cardEl.getAttribute('data-stage') || '';
          filterState.overdueOnly = false;
          els.stageFilter.value = els.stageFilter.value === stage ? '' : stage;
          renderAll();
          const hash = els.stageFilter.value ? `#${slugify(els.stageFilter.value)}` : '';
          history.replaceState(null, '', `${window.location.pathname}${hash}`);
          els.stageDetail.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      });
      gridEl.querySelectorAll('.stage-overdue-button').forEach((buttonEl) => {
        buttonEl.addEventListener('mouseenter', () => {
          buttonEl.closest('.stage-card')?.classList.add('hover-locked');
        });
        buttonEl.addEventListener('mouseleave', () => {
          buttonEl.closest('.stage-card')?.classList.remove('hover-locked');
        });
        buttonEl.addEventListener('blur', () => {
          buttonEl.closest('.stage-card')?.classList.remove('hover-locked');
        });
        buttonEl.addEventListener('click', (event) => {
          event.stopPropagation();
          const stage = buttonEl.getAttribute('data-overdue-stage') || '';
          if (filterState.overdueOnly && els.stageFilter.value === stage) {
            filterState.overdueOnly = false;
            els.stageFilter.value = '';
          } else {
            filterState.overdueOnly = true;
            els.stageFilter.value = stage;
          }
          renderAll();
          els.stageDetail.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      });
    }

    function renderStageDetail() {
      const stage = selectedStage();
      const baseRows = rowsForSummary();
      if (!stage) {
        const overdueRows = baseRows.filter((row) => row.is_over_sla);
        els.stageDetail.innerHTML = `
          <div class="stage-detail-title">All Buckets</div>
          <div class="stage-detail-copy">The top layout is split into Onboarding, EP Ops, and EP Installation. Onboarding runs from New Intake through Dealer Approval, EP Ops runs from Stamped through Pending Install, EP Installation runs from Post Install through PTO, and hold/cancel/archive-style buckets stay in the lower lane.</div>
          <div class="stage-detail-copy">There are <strong>${overdueRows.length}</strong> total overdue project(s) across SLA-tracked buckets. Use <strong>Show Overdue Only</strong> or click the overdue count on a card to jump straight into the flagged work.</div>
        `;
        return;
      }
      const detail = stageCards.find((card) => card.stage === stage);
      if (!detail) return;
      const detailRows = baseRows.filter((row) => row.pm_bucket === stage);
      const overdueRows = detailRows.filter((row) => row.is_over_sla);
      const slaBucketLabel = detail.sla_label ? ` (${detail.sla_label})` : '';
      const slaCopy = detail.sla_mode === 'zip'
        ? 'SLA is assigned per project from its address ZIP code using the permit TAT sheet.'
        : detail.sla_days
          ? `SLA is <strong>${detail.sla_days}</strong> day${detail.sla_days === 1 ? '' : 's'} for this bucket${slaBucketLabel}.`
          : 'No SLA is configured for this bucket yet.';
      els.stageDetail.innerHTML = `
        <div class="stage-detail-title">${escapeHtml(detail.stage)}</div>
        <div class="stage-detail-copy">${escapeHtml(detail.count)} active Happy Slr job(s) currently sit in this Process Board bucket. ${slaCopy}</div>
        <div class="stage-detail-copy"><strong>${overdueRows.length}</strong> of those project(s) are currently over SLA.</div>
      `;
    }

    function renderTable() {
      const list = sortedRows(filteredRows());
      const overdueShown = list.filter((row) => row.is_over_sla).length;
      els.tableMeta.textContent = `${list.length} of ${rows.length} jobs shown • ${overdueShown} overdue`;
      if (!list.length) {
        els.tableBody.innerHTML = '<tr><td colspan="23" class="empty-state">No jobs match the selected filters.</td></tr>';
        return;
      }
      els.tableBody.innerHTML = list.map((row) => {
        const nameCell = row.board_url
          ? `<a class="name-link" href="${escapeHtml(row.board_url)}" target="_blank" rel="noreferrer">${escapeHtml(row.display_name)}</a>`
          : escapeHtml(row.display_name);
        const slaText = hasSla(row)
          ? `${escapeHtml(String(row.sla_days))} day${Number(row.sla_days) === 1 ? '' : 's'}${row.uses_default_permit_sla ? ' (default)' : ''}`
          : '—';
        const overdueText = row.is_over_sla ? 'Flagged' : 'On Time';
        const rowClass = row.is_over_sla ? 'overdue-row' : '';
        return `
          <tr class="${rowClass}">
            <td><span class="stage-pill">${escapeHtml(row.pm_bucket || '')}</span></td>
            <td>${nameCell}</td>
            <td>${escapeHtml(row.assigned_rep || '')}</td>
            <td>${escapeHtml(row.address || '')}</td>
            <td>${escapeHtml(row.zip_code || '')}</td>
            <td>${escapeHtml(row.permit_ahj || '')}</td>
            <td>${escapeHtml(row.permit_phone || '')}</td>
            <td>${escapeHtml(row.permit_tat || '')}</td>
            <td>${escapeHtml(row.site_survey_date || '')}</td>
            <td>${escapeHtml(row.first_installed_on || '')}</td>
            <td>${escapeHtml(row.task_status || '')}</td>
            <td>${escapeHtml(row.calc_status || '')}</td>
            <td>${escapeHtml(row.finance_status || '')}</td>
            <td>${escapeHtml(row.permit_status || '')}</td>
            <td>${escapeHtml(row.interconnection_status || '')}</td>
            <td>${escapeHtml(row.monitoring_approval || '')}</td>
            <td>${escapeHtml(row.monitoring_status || '')}</td>
            <td class="note-cell">${escapeHtml(row.process_board_note || '')}</td>
            <td class="note-cell">${escapeHtml(row.essential_view_note || '')}</td>
            <td>${escapeHtml(row.created_at_display || '')}</td>
            <td>${escapeHtml(row.days_in_bucket || 0)}</td>
            <td>${slaText}</td>
            <td>${overdueText}</td>
          </tr>
        `;
      }).join('');
    }

    function renderAll() {
      renderOverview();
      els.overdueToggle.classList.toggle('active', filterState.overdueOnly);
      renderStageFilterOptions(cardsForDisplay(stageCards));
      renderStageCards(els.onboardingStageGrid, onboardingStageCards);
      renderStageCards(els.epOpsStageGrid, epOpsStageCards);
      renderStageCards(els.epInstallationStageGrid, epInstallationStageCards);
      renderStageCards(els.secondaryStageGrid, secondaryStageCards);
      renderStageDetail();
      renderTable();
      syncTableScrollbar();
    }

    els.searchFilter.addEventListener('input', renderAll);
    els.assignedRepToggle.addEventListener('click', () => {
      const opening = els.assignedRepMenu.hidden;
      els.assignedRepMenu.hidden = !opening;
      els.assignedRepToggle.setAttribute('aria-expanded', String(opening));
    });
    els.assignedRepMenu.addEventListener('change', () => {
      updateAssignedRepLabel();
      renderAll();
    });
    document.addEventListener('click', (event) => {
      if (!els.assignedRepFilter.contains(event.target)) {
        els.assignedRepMenu.hidden = true;
        els.assignedRepToggle.setAttribute('aria-expanded', 'false');
      }
    });
    els.stageFilter.addEventListener('change', renderAll);
    els.createdYearFilter.addEventListener('change', renderAll);
    els.overdueToggle.addEventListener('click', () => {
      filterState.overdueOnly = !filterState.overdueOnly;
      renderAll();
    });
    els.tableWrap.addEventListener('scroll', () => {
      els.tableScrollbar.scrollLeft = els.tableWrap.scrollLeft;
    });
    els.tableScrollbar.addEventListener('scroll', () => {
      els.tableWrap.scrollLeft = els.tableScrollbar.scrollLeft;
    });
    window.addEventListener('resize', syncTableScrollbar);
    els.resetFilters.addEventListener('click', () => {
      els.searchFilter.value = '';
      if (els.assignedRepSearch) { els.assignedRepSearch.value = ''; filterRepMenu(els.assignedRepMenu, ''); }
      els.assignedRepMenu.querySelectorAll('input:checked').forEach((input) => { input.checked = false; });
      updateAssignedRepLabel();
      els.stageFilter.value = '';
      els.createdYearFilter.value = '';
      filterState.overdueOnly = false;
      history.replaceState(null, '', window.location.pathname);
      renderAll();
    });
    els.openCancellationModal.addEventListener('click', openCancellationModal);
    els.cancellationRepToggle.addEventListener('click', () => {
      const opening = els.cancellationRepMenu.hidden;
      els.cancellationRepMenu.hidden = !opening;
      els.cancellationRepToggle.setAttribute('aria-expanded', String(opening));
    });
    els.cancellationRepMenu.addEventListener('change', () => {
      updateCancellationRepLabel();
      renderCancellationChart();
    });
    document.addEventListener('click', (event) => {
      if (!els.cancellationRepFilter.contains(event.target)) {
        els.cancellationRepMenu.hidden = true;
        els.cancellationRepToggle.setAttribute('aria-expanded', 'false');
      }
    });
    els.closeCancellationModal.addEventListener('click', closeCancellationModal);
    els.cancellationModal.addEventListener('click', (event) => {
      if (event.target === els.cancellationModal) {
        closeCancellationModal();
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !els.cancellationModal.hidden) {
        closeCancellationModal();
      }
    });


    if (els.assignedRepSearch) {
      els.assignedRepSearch.addEventListener('input', () => {
        filterRepMenu(els.assignedRepMenu, els.assignedRepSearch.value);
      });
      els.assignedRepSearch.addEventListener('click', (event) => event.stopPropagation());
    }
    if (els.cancellationRepSearch) {
      els.cancellationRepSearch.addEventListener('input', () => {
        filterRepMenu(els.cancellationRepMenu, els.cancellationRepSearch.value);
      });
      els.cancellationRepSearch.addEventListener('click', (event) => event.stopPropagation());
    }
    els.assignedRepToggle.addEventListener('click', () => {
      if (!els.assignedRepMenu.hidden && els.assignedRepSearch) {
        els.assignedRepSearch.focus();
      }
    });
    els.cancellationRepToggle.addEventListener('click', () => {
      if (!els.cancellationRepMenu.hidden && els.cancellationRepSearch) {
        els.cancellationRepSearch.focus();
      }
    });

        renderCreatedYearFilterOptions();
    renderAll();
