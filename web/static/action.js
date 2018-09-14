DEBOUNCE_TIMEOUT = 500;

const desc = {
  data: {
    searchStr: '',
    focusOnInput: false,
    debouncer: null,
    curIter: 0,

    list: [],
    info: null,
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
      const iter = ++this.curIter;
      if(this.searchStr === "") {
        this.info = null;
        this.list = [];
        return;
      }

      const segs = this.searchStr.split(" ").join("+");
      const resp = await fetch(`/search/${segs}/${page}`);
      const payload = await resp.json();

      if(iter !== this.curIter) return;

      this.list = payload.result;
      this.info = {
        time: payload.time,
        pages: payload.pages,
        curPage: page,
      };
    },

    async refresh() {
      this.goto(1);
    },

    tryPage(p) {
      if(!Number.isInteger(p)) return;

      this.goto(p);
    },

    async load(id) {
      await fetch(`/fetch/${id}`)
    },

    jiegeRainbow(e, active) {
      if(e === "J" || e === "G") return "#2196f3"
      if(e === "e") {
        if(active) return "#b71c1c"
        else return "#f57f17"
      } else return "#1b5e20"
    },
  },

  computed: {
    vacantInput() {
      return !this.searchStr && !this.focusOnInput;
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
  }
};

function bootstrap() {
  const inst = new Vue(desc);
  inst.$mount("#app");
}
