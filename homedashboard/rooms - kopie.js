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
		result = false
		
		if (isDefined(this.item.devices)){
			if (this.item.devices.length > 0){
				for (const d of this.item.devices) {
					if (d.open_close == 1){
						return true
					}
					else{
						result = false
					}
				}
			}
		}
		// if (isDefined(this.item.airco)){
		// 	if (this.item.airco.length > 0){
		// 		if (this.item.airco[0].open_close == 1){
		// 			result = true
		// 		}
		// 		else{
		// 			result = false
		// 		}
		// 	}
		// }
		return result
    },
  	open_close_error() {
		result = false
		
		if (isDefined(this.item.devices)){
			if (this.item.devices.length > 0){
				for (const d of this.item.devices) {
					if (d.open_close == 99){
						return true
					}
					else{
						result = false
					}
				}
		}
		return result
		}
  	},
  	open_close_airco() {
		result = false
		
		if (isDefined(this.item.devices)){
			if (this.item.devices.length > 0){
				for (const d of this.item.devices) {
					if (d.name == 'airco'){
						if (d.open_close == 1){
							return true
						}
						else{
							return false
						}
					}
				}
			}
		}
		return result
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
			this.item.tmp_hand = this.item.ingesteld
		}
		
	}
  },
  template: "<div :id='tidid' @click=\"this.select_kamer\" v-bind:class=\"[ open_close == true ? [ open_close_error ? 'radactive kamer error' : 'radactive kamer' ] : [ open_close_error ? 'radinactive kamer error' : 'radinactive kamer' ], [ this.item.handmatig == true ? 'handmatig' : this.item.exclude == true ? 'holiday' : 'automaat' ], [ open_close_airco ? 'airco' : '' ], [ this.item.lowbattery == true ? 'lowbat' : '' ] ]\"><div class=\"kamer_title\">{{ item.naam }}</div><div class=\"kamer_sub\"><div v-bind:class=\"[ this.item.insync == false ? 'kamer_curtemp error' : 'kamer_curtemp' ]\">{{ item.huidig }}&#176;</div><div class=\"kamer_newtemp\">{{ item.ingesteld }}&#176;</div></div></div>"
}