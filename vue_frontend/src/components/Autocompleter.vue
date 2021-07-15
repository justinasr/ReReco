<template>
  <div style="position: relative">
    <input type="text"
           v-model="realValue"
           :disabled="disabled"
           @focus="makeFocused(true)"
           @blur="makeFocused(false)"
           @input="updateValue()"
           v-on:keydown.up.capture.prevent="arrowKey(-1)"
           v-on:keydown.down.capture.prevent="arrowKey(1)"
           v-on:keydown.enter.capture.prevent="enterKey()">
    <v-progress-circular
      :size="18"
      :width="2"
      style="margin: 4px 0; position: absolute; right: 4px;"
      color="primary"
      indeterminate
      v-if="getSuggestionsTimer || loading"
    ></v-progress-circular>
    <div class="suggestion-list-wrapper"
         @mouseover="mouseEnteredList(true)"
         @mouseleave="mouseEnteredList(false)">
      <div class="elevation-3 suggestion-list">
        <div v-for="(item, index) in items"
             :key="index"
             class="suggestion-item"
             @click="select(item)"
             @mouseover="mouseEnteredItem(index)"
             v-bind:class="{'suggestion-item-hover': index == selectedIndex}"
             v-html="highlight(item)"></div>
      </div>
    </div>
  </div>
</template>

<script>

/* component needs to do to be compatible with v-model
   is accept a :value property and emit an @input event
   when the user changes the value.
*/

  export default {
    props:{
      value: String,
      identifier: String,
      getSuggestions: Function,
      onBlur: Function,
      onSelect: Function,
      disabled: {
        type: Boolean,
        default: false,
      }
    },
    data () {
      return {
        getSuggestionsWait: 250, // Milliseconds to wait before fetching suggestions
        items: [],
        savedItems: [],
        isFocused: false,
        loading: false,
        realValue: undefined,
        mouseInside: false,
        getSuggestionsTimer: undefined,
        ignoreChange: false,
        selectedIndex: 0,
      }
    },
    created () {
      this.realValue = this.value;
    },
    watch: {
      isFocused (focused) {
        if (!focused) {
          this.savedItems = this.items;
          this.items = [];
          if (this.onBlur) {
            this.onBlur(this.identifier, this.realValue);
          }
        } else {
          this.items = this.savedItems;
          this.savedItems = [];
        }
      },
      value (value) {
        this.realValue = value;
      },
      realValue (value) {
        this.selectedIndex = 0;
        if (!this.isFocused) {
          return;
        }

        if (this.ignoreChange) {
          this.ignoreChange = false;
          return;
        }

        if (!value || !value.length) {
          this.items = [];
          return
        }
        
        if (this.getSuggestions) {
          if (this.getSuggestionsTimer) {
            clearTimeout(this.getSuggestionsTimer);
            this.getSuggestionsTimer = undefined;
          }
          this.items = [];
          this.getSuggestionsTimer = setTimeout(() => {
            const component = this;
            this.loading = true;
            component.getSuggestions(this.identifier, value, function(items) {
              items = items.filter(s => s != component.realValue);
              component.items = items;
              component.getSuggestionsTimer = undefined;
              component.loading = false;
            });
          }, this.getSuggestionsWait);
        }
      },
    },
    methods: {
      select (value) {
        this.ignoreChange = true;
        this.realValue = value;
        this.items = [];
        this.updateValue();
        if (this.onSelect) {
          this.onSelect(this.identifier, this.realValue);
        }
      },
      updateValue () {
        this.$emit('input', this.realValue);
      },
      makeFocused (focused) {
        if (!this.mouseInside || focused) {
          this.isFocused = focused;
        }
      },
      mouseEnteredList (entered) {
        this.mouseInside = entered;
      },
      mouseEnteredItem (index) {
        this.selectedIndex = index;
      },
      highlight (item) {
        const splitValues = this.realValue.toLowerCase().split(' ').filter(Boolean);
        let highlighted = '';
        let lastIndex = 0;
        const lowerCaseItem = item.toLowerCase();
        for (let split of splitValues) {
          let foundIndex = lowerCaseItem.indexOf(split, lastIndex);
          if (foundIndex < 0) {
            continue;
          }
          highlighted += item.slice(lastIndex, foundIndex);
          lastIndex += foundIndex - lastIndex;
          let highlightedPiece = item.slice(foundIndex, foundIndex + split.length);
          highlighted += '<b style="background: #dadada">' + highlightedPiece + '</b>';
          lastIndex += split.length;
        }
        highlighted += item.slice(lastIndex);
        return highlighted;
      },
      arrowKey (direction) {
        const itemsLength = this.items.length;
        if (!itemsLength) {
          this.selectedIndex = 0;
          return;
        }
        this.selectedIndex = (itemsLength + this.selectedIndex + direction) % itemsLength;
      },
      enterKey (){
        if (!this.items.length) {
          return;
        }
        this.select(this.items[this.selectedIndex]);
      }
    }
  }
</script>

<style scoped>

.suggestion-list-wrapper {
  position: relative;
  z-index: 100;
}

.suggestion-list {
  margin: 2px;
  width: calc(100% - 4px);
  background: #fff;
  position: absolute;
  cursor: pointer;
}

.suggestion-item {
  padding: 4px;
  margin-top: 2px;
  margin-bottom: 2px;
}

.suggestion-item-hover {
  background: #eeeeee;
}

</style>
