function isDefined(x) {
    var undefined;
    return x !== undefined;
}
const Rooms = {
  props: ['item', 'type'],
  computed: {
    tidid() {
      //this.tid = "tid_"+this.item.tid
	  return "kid_"+this.item.tid
    },
    open_close() {
		if (isDefined(this.item.radiator)){
			if (this.item.radiator[0].open_close == 1){
				return true
			}
			else{
				return false
			}
		}
    }
  },
  methods: {
	select_kamer(){
		if (this.$parent.activetab != 4){
			fetch(this.$root.url+'/kamerschema?nr='+this.item.tid)
			.then(response => response.json())
			.then(json => {
				this.$parent.schema_obj = json
				this.$parent.activekmr = this.item.tid
			})
		}
		else{
			this.$parent.activekmr_cfg = this.item.tid
		}
		
	}
  },
  template: "<div :id='tidid' @click=\"this.select_kamer\" v-bind:class=\"[ open_close == true ? [ this.item.radiator[0].open_close == 99 ? 'radactive kamer error' : 'radactive kamer' ] : [ this.item.radiator[0].open_close == 99 ? 'radinactive kamer error' : 'radinactive kamer' ], [ this.item.handmatig == true ? 'handmatig' : 'automaat' ], [ this.item.lowbattery == true ? 'lowbat' : '' ] ]\"><div class=\"kamer_title\">{{ item.naam }}</div><div class=\"kamer_sub\"><div v-bind:class=\"[ this.item.insync == false ? 'kamer_curtemp error' : 'kamer_curtemp' ]\">{{ item.huidig }}&#176;</div><div class=\"kamer_newtemp\">{{ item.ingesteld }}&#176;</div></div></div>"
}