function isDefined(x) {
    var undefined;
    return x !== undefined;
}
const Programs = {
  props: ['item', 'type'],
  computed: {
    beschr() {
    	if (this.item==this.$root.nieuwe_zone){
			return "+"
		}
		else{
			return this.item.beschrijving
		}
		
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
	wateringstatus(){
		if (this.$root.water_obj.watering == false){
			return 'cvinactive showstatus_box'
		}
		else{
			if (this.$vnode.key == this.$root.water_obj.cur_program){
				return 'cvactive showstatus_box'
			}
			else{
				return 'cvinactive showstatus_box'
			}
		}
	},
	select_prog(){
		//if this zone was already selected, start the program, else just select it
		if (this.$root.activeprog == (this.$vnode.key+1)){
			if (this.$root.activeprog != 1){ //unless it is the manual one
				if (this.$el.children[0].classList.contains("cvactive")){
					console.log("stop watering program: "+this.$vnode.key)
					this.$el.children[0].classList.remove("cvactive")
					fetch(this.$root.ip+'/watering?action=stop&value='+this.$vnode.key+';0')//http://192.168.0.125/watering?action=start&value=1;0
					.then(response => response.json())
					.then(json => {
						this.$root.watering_status = false
						this.$root.water_obj = json
					})
					this.$root.timer = setInterval(this.$root.fetchwaterstatus, 60000)
				}
				else{
					this.$el.children[0].classList.add("cvactive")
					console.log("start watering program: "+this.$vnode.key)
					fetch(this.$root.ip+'/watering?action=start&value='+this.$vnode.key+';0')//http://192.168.0.125/watering?action=start&value=1;0
					.then(response => response.json())
					.then(json => {
						this.$root.watering_status = false
						this.$root.water_obj = json
					})
					this.$root.timer = setInterval(this.$root.fetchwaterstatus, 5000)
				}				
			}
		}
		else{
			this.$root.zone_obj = this.item.zones
			this.$root.activeprog = this.$vnode.key+1	
		}		
	}
  },
  template: `<div><div @click="this.select_prog" v-bind:class="this.wateringstatus()">
	  <div class="status_box_title">{{this.beschr}}
	  
	  </div>
  </div></div>`
}
//<div class=\"\"><zones v-for=\"(v, index) in item.zones\" :item=\"v\" :key=\"index\"></zones></div>