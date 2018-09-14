DEBOUNCE_TIMEOUT = 500;

const TIMER_RE = /^\d\d\d\d-\d\d-\d\d$/

const desc = {
  data: {
    searchStr: '',
    focusOnInput: false,
    debouncer: null,
    curIter: 0,

    lower: "",
    higher: "",

    running: false,

    rendering: null,

    list: [],
    info: null,
  },

  created() {
    this.goto(1);
  },

  methods: {
    scheduleRefresh() {
      if(this.debouncer !== null) clearTimeout(this.debouncer);
      this.debouncer = setTimeout(() => {
        this.refresh();
        this.debouncer = null;
      }, DEBOUNCE_TIMEOUT);
    },

    async goto(page) {
      this.running = true;
      const iter = ++this.curIter;
      let url;
      if(this.searchStr === "")
        url = `/all/${page}`;
      else {
        const segs = this.searchStr.split(" ").filter(e => e.length > 0).join("+");
        url = `/search/${segs}/${page}`;
      }

      if(this.lower.match(TIMER_RE) && this.higher.match(TIMER_RE))
        url += `?lower=${this.lower}&higher=${this.higher}`;

      const resp = await fetch(url);
      const payload = await resp.json();

      if(iter !== this.curIter) return;

      this.list = payload.result;
      this.info = {
        time: payload.time,
        pages: payload.pages,
        total: payload.total,
        curPage: page,
      };
      this.running = false;
    },

    async refresh() {
      this.goto(1);
    },

    tryPage(p) {
      if(!Number.isInteger(p)) return;

      this.goto(p);
    },

    async load(id) {
      this.rendering = null;
      const resp = await fetch(`/fetch/${id}`)
      const payload = await resp.json();
      this.rendering = payload;
      document.body.style['overflow-y'] = 'hidden';
    },

    dismiss() {
      this.rendering = null;
      document.body.style['overflow-y'] = 'auto';
    },

    jiegeRainbow(e, active) {
      if(e === "J" || e === "G") return "#2196f3"
      if(e === "e") {
        if(active) return "#b71c1c"
        else return "#f57f17"
      } else return "#1b5e20"
    },

    renderPager(e, important) {
      if(!Number.isInteger(e)) return e;
      const s = String(e);
      if(s.length <= 2) return s;
      else if(important) return s;
      return '..' + s.substr(s.length-1);
    },

    highlight(content) {
      if(this.searchStr === '') return content;
      const segs = this.searchStr.split(' ').filter(e => e.length > 0);
      for(const s of segs)
        content = content.split(s).join(`<span class="hl">${s}</span>`);
      return content;
    },
  },

  computed: {
    vacantInput() {
      return !this.searchStr && this.focusOnInput;
    },

    pagerSpec() {
      if(this.info === null) return null;
      if(this.info.pages === 0) return null;

      const unpadded = [];
      let missingFirst = true;
      let missingLast = true;
      let activeSlot = 0;

      for(let i = -2; i <= 2; ++i) {
        page = this.info.curPage + i;
        if(page <= 0 || page > this.info.pages) continue;

        unpadded.push(page);
        if(page === 1) missingFirst = false;
        if(page === this.info.pages) missingLast = false;
        if(i === 0) activeSlot = unpadded.length -1+2;
      }

      const top = ['J', 'i'].concat(new Array(unpadded.length).fill('e')).concat(['G', 'e']);
      const front = missingFirst ? [1, '..'] : ['', ''];
      const back = missingLast ? ['..', this.info.pages] : ['', ''];
      const bottom = front.concat(unpadded).concat(back);

      return { top, bottom, activeSlot };
    },

    timeError() {
      if(!this.lower && !this.higher) return false;
      if(!this.lower.match(TIMER_RE))
        return true
      if(!this.higher.match(TIMER_RE))
        return true

      return false
    },
  }
};

function bootstrap() {
  const inst = new Vue(desc);
  inst.$mount("#app");
}
