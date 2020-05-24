export const listLengthMixin = {

  methods: {
    listLength(l) {
      if (!l) {
        return 0;
      }
      if (typeof(l) === "string") {
        return l.split('\n').filter(Boolean).length;
      }
      return l.length;
    },
  }
}