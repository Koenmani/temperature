const Balk = {
  props: ['item'],
  computed: {
  		
  },
  methods: {
	select_time(event){
		if (!this.$root.showpopup){
			this.$root.activeschema = this.item.id
			this.$root.showpopup = true
			this.$root.popupleft = (event.clientX-100) + "px"
			this.$root.popuptop = (event.clientY-150) + "px"
			this.$root.popuparrowleft = this.$el.getBoundingClientRect().left + this.$el.getBoundingClientRect().width - 50
			this.$root.popuparrowright = this.$el.getBoundingClientRect().left + this.$el.getBoundingClientRect().width 
			this.$root.popuparrowtop = this.$el.getBoundingClientRect().top - 10
			
			this.$root.old_schema_obj = Object.assign({}, this.$root.schema_obj[parseInt(this.item.id.split("_")[3])]);
			this.$root.old_temp_obj = this.$root.schema_obj[parseInt(this.item.id.split("_")[3])-1].temp
		}
	}	
  },
  template: "<div class=\"balk\" @click=\"select_time($event)\" v-bind:id=\"item.id\" v-bind:style=\"{ width: item.w + '%', left: item.l + '%',backgroundColor:item.c }\"></div>"
}