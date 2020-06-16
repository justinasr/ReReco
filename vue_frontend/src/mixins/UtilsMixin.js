export const utilsMixin = {

  methods: {
    listLength(list) {
      if (!list) {
        return 0;
      }
      if (typeof(list) === "string") {
        return list.split('\n').filter(Boolean).length;
      }
      return list.length;
    },
    makeCopy(obj) {
      return JSON.parse(JSON.stringify(obj));
    }
  }
}